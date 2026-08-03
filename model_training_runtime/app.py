"""HTTP contract validation service for the exploratory training-code runtime."""
from __future__ import annotations

import secrets
import shutil
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import Body, Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from admission import (
    ContractAdmissionError,
    validate_execution_admission,
    validate_package_manifest,
    validate_result_admission,
)
from coordinator import ExecutionCoordinator, ExecutionCoordinatorError
from contracts import (
    DATASET_PROTOCOL_VERSION,
    DATASET_SOURCE_PROTOCOL_VERSION,
    EVENT_PROTOCOL_VERSION,
    EXECUTION_PROTOCOL_VERSION,
    MODEL_PACKAGE_PROTOCOL_VERSION,
    PACKAGE_PROTOCOL_VERSION,
    RESULT_PROTOCOL_VERSION,
    SUBMISSION_PROTOCOL_VERSION,
    TrainingCodeSubmission,
    CheckpointEvent,
    LogEvent,
    MetricEvent,
    PhaseEvent,
    TrainingDatasetManifest,
    TrainingDatasetSourceManifest,
    TrainingExecutionRequest,
    TrainingModelPackageManifest,
    TrainingPackageManifest,
    TrainingResult,
)
from package_validation import (
    ArchiveValidationReport,
    ModelPackageArchiveValidationReport,
    PackageArchiveValidationError,
    validate_model_package_archive,
    validate_package_archive,
)
from registry import PackageRegistryError, TrainingPackageRegistry
from runtime import (
    ManagedRuntimeSpec,
    RuntimeExecutionSettings,
    ServiceSubprocessExecutor,
    TrainingRuntimeManager,
)
from storage import OpenDalS3Storage, load_model_training_runtime_config
from artifacts import PersistedArtifact, persist_execution_artifacts
from execution_policy import ExecutionPolicyError, validate_execution_policy
from mq_consumer import TrainingCodeConsumer
from runtime.logging_utils import logger


SERVICE_NAME = "model-training-runtime"
SERVICE_VERSION = "0.1.0-experimental"


class ValidationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool = True
    contract: str
    normalized: dict[str, Any]


class ExecutionAdmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: TrainingPackageManifest
    execution: TrainingExecutionRequest


class ResultAdmissionRequest(ExecutionAdmissionRequest):
    result: TrainingResult


class ArchiveInspectionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    file_count: int = Field(ge=0)
    uncompressed_bytes: int = Field(ge=0)


class TrainingCodePackageInspectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["training_code_package"]
    valid: Literal[True] = True
    archive: ArchiveInspectionMetadata
    configuration: TrainingPackageManifest


class TrainingModelPackageInspectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["training_model_package"]
    valid: Literal[True] = True
    archive: ArchiveInspectionMetadata
    configuration: TrainingModelPackageManifest


class DirectExecutionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_id: str
    result: TrainingResult
    events: list[dict[str, Any]]
    logs: list[dict[str, Any]]
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    workspace_cleaned: bool = True


def validated_response(contract: str, value: Any) -> ValidationResponse:
    return ValidationResponse(
        contract=contract,
        normalized=value.model_dump(mode="json"),
    )


def archive_inspection_response(
    *,
    kind: str,
    report: ArchiveValidationReport | ModelPackageArchiveValidationReport,
) -> dict[str, Any]:
    """Return the validated manifest in a stable, presentation-oriented envelope."""
    return {
        "kind": kind,
        "valid": True,
        "archive": {
            "sha256": report.sha256,
            "file_count": report.file_count,
            "uncompressed_bytes": report.uncompressed_bytes,
        },
        "configuration": report.manifest.model_dump(mode="json"),
    }


def _execution_is_enabled(config: dict[str, Any]) -> bool:
    execution = config.get("execution")
    return config.get("enabled") is True and isinstance(execution, dict) and execution.get("enabled") is True


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Start and stop the custom-training MQ consumer with this API service."""
    consumer = TrainingCodeConsumer()
    application.state.training_code_consumer = consumer
    if _execution_is_enabled(load_model_training_runtime_config()):
        consumer.start()
        logger.info("Training code MQ consumer started with the Runtime service")
    else:
        logger.info("Training code MQ consumer is disabled by configuration")
    try:
        yield
    finally:
        consumer.stop()
        application.state.training_code_consumer = None


app = FastAPI(
    title="Model Training Runtime",
    description=(
        "Experimental in-service model training runtime. It validates versioned "
        "training packages and can execute approved packages in a bounded subprocess."
    ),
    version=SERVICE_VERSION,
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, Any]:
    config = load_model_training_runtime_config()
    execution_enabled = _execution_is_enabled(config)
    consumer = getattr(app.state, "training_code_consumer", None)
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "mode": "in_service_execution" if execution_enabled else "contract_validation_only",
        "execution_enabled": execution_enabled,
        "mq_consumer_enabled": execution_enabled,
        "mq_consumer_running": bool(consumer and consumer.is_running),
        "mq_consumer_connected": bool(consumer and consumer.is_connected),
        "mq_consumer_active_executions": consumer.active_executions if consumer else 0,
    }


@app.get("/v1/contracts")
async def list_contracts() -> dict[str, Any]:
    return {
        "service": SERVICE_NAME,
        "experimental": True,
        "contracts": {
            "package": PACKAGE_PROTOCOL_VERSION,
            "dataset_manifest": DATASET_PROTOCOL_VERSION,
            "dataset_source_manifest": DATASET_SOURCE_PROTOCOL_VERSION,
            "model_package": MODEL_PACKAGE_PROTOCOL_VERSION,
            "execution": EXECUTION_PROTOCOL_VERSION,
            "event": EVENT_PROTOCOL_VERSION,
            "result": RESULT_PROTOCOL_VERSION,
            "mq_submission": SUBMISSION_PROTOCOL_VERSION,
        },
    }


@app.post("/v1/contracts/package/validate", response_model=ValidationResponse)
async def validate_package(manifest: TrainingPackageManifest) -> ValidationResponse:
    _ensure_admitted(lambda: validate_package_manifest(manifest))
    return validated_response(PACKAGE_PROTOCOL_VERSION, manifest)


@app.post("/v1/packages/archive/validate")
async def validate_package_archive_endpoint(
    archive: bytes = Body(media_type="application/zip"),
) -> dict[str, Any]:
    """Validate a ZIP package layout and manifest without importing its Python files."""
    try:
        report = validate_package_archive(archive)
    except PackageArchiveValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"valid": True, **report.as_dict()}


@app.post(
    "/v1/packages/archive/inspect",
    response_model=TrainingCodePackageInspectionResponse,
)
async def inspect_package_archive_endpoint(
    archive: bytes = Body(media_type="application/zip"),
) -> TrainingCodePackageInspectionResponse:
    """Read validated package configuration without importing or returning package code."""
    try:
        report = validate_package_archive(archive)
    except PackageArchiveValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return TrainingCodePackageInspectionResponse(
        **archive_inspection_response(kind="training_code_package", report=report)
    )


@app.post("/v1/model-packages/archive/validate")
async def validate_model_package_archive_endpoint(
    archive: bytes = Body(media_type="application/zip"),
) -> dict[str, Any]:
    """Inspect an imported model ZIP without loading framework-specific bytes."""
    try:
        report = validate_model_package_archive(archive)
    except PackageArchiveValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"valid": True, **report.as_dict()}


@app.post(
    "/v1/model-packages/archive/inspect",
    response_model=TrainingModelPackageInspectionResponse,
)
async def inspect_model_package_archive_endpoint(
    archive: bytes = Body(media_type="application/zip"),
) -> TrainingModelPackageInspectionResponse:
    """Read validated model-package configuration without deserializing model bytes."""
    try:
        report = validate_model_package_archive(archive)
    except PackageArchiveValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return TrainingModelPackageInspectionResponse(
        **archive_inspection_response(kind="training_model_package", report=report)
    )


@app.post("/v1/contracts/dataset-manifest/validate", response_model=ValidationResponse)
async def validate_dataset_manifest(manifest: TrainingDatasetManifest) -> ValidationResponse:
    return validated_response(DATASET_PROTOCOL_VERSION, manifest)


@app.post("/v1/contracts/dataset-source-manifest/validate", response_model=ValidationResponse)
async def validate_dataset_source_manifest(
    manifest: TrainingDatasetSourceManifest,
) -> ValidationResponse:
    return validated_response(DATASET_SOURCE_PROTOCOL_VERSION, manifest)


@app.post("/v1/contracts/execution/validate", response_model=ValidationResponse)
async def validate_execution(request: TrainingExecutionRequest) -> ValidationResponse:
    return validated_response(EXECUTION_PROTOCOL_VERSION, request)


@app.post("/v1/admission/execution/validate")
async def validate_execution_admission_endpoint(request: ExecutionAdmissionRequest) -> dict[str, Any]:
    _ensure_admitted(lambda: validate_execution_admission(request.manifest, request.execution))
    return {"valid": True, "scope": "package_execution"}


@app.post("/v1/contracts/event/validate", response_model=ValidationResponse)
async def validate_event(
    event: Annotated[
        PhaseEvent | LogEvent | MetricEvent | CheckpointEvent,
        Body(discriminator="event_type"),
    ],
) -> ValidationResponse:
    return validated_response(EVENT_PROTOCOL_VERSION, event)


@app.post("/v1/contracts/result/validate", response_model=ValidationResponse)
async def validate_result(result: TrainingResult) -> ValidationResponse:
    return validated_response(RESULT_PROTOCOL_VERSION, result)


@app.post("/v1/admission/result/validate")
async def validate_result_admission_endpoint(request: ResultAdmissionRequest) -> dict[str, Any]:
    _ensure_admitted(
        lambda: validate_result_admission(request.manifest, request.execution, request.result)
    )
    return {"valid": True, "scope": "package_execution_result"}


@app.post("/v1/contracts/mq-submission/validate", response_model=ValidationResponse)
async def validate_mq_submission(submission: TrainingCodeSubmission) -> ValidationResponse:
    return validated_response(SUBMISSION_PROTOCOL_VERSION, submission)


def get_package_registry() -> TrainingPackageRegistry:
    """Create the OpenDAL registry only when an explicit registration endpoint is called."""
    return TrainingPackageRegistry(OpenDalS3Storage())


def require_registration_authorization(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Protect state-changing registry calls when an internal token is configured."""
    config = load_model_training_runtime_config()
    expected_token = str(config.get("token", "") or "").strip()
    if not expected_token:
        return
    expected_header = f"Bearer {expected_token}"
    if authorization is None or not secrets.compare_digest(authorization, expected_header):
        raise HTTPException(status_code=401, detail="invalid model training runtime registration token")


def get_training_coordinator() -> tuple[ExecutionCoordinator, Path]:
    """Build the first in-service executor from Nacos-owned runtime settings."""
    config = load_model_training_runtime_config()
    execution_config = config.get("execution") if isinstance(config.get("execution"), dict) else {}
    if execution_config.get("enabled") is not True:
        raise HTTPException(
            status_code=503,
            detail="in-service training execution is disabled by model-training-runtime.execution.enabled",
        )

    runtime_ids = execution_config.get(
        "runtime_ids",
        ["ultralytics-8.3.0-pytorch-2.5-cu124", "pytorch-2.5-cu124"],
    )
    if isinstance(runtime_ids, str):
        runtime_ids = [runtime_ids]
    if not isinstance(runtime_ids, list) or not all(isinstance(value, str) and value.strip() for value in runtime_ids):
        raise HTTPException(status_code=503, detail="training runtime execution.runtime_ids is invalid")

    python_executable = Path(str(execution_config.get("python_executable") or sys.executable)).resolve()
    workspace_root = Path(
        str(
            execution_config.get(
                "workspace_root",
                Path(tempfile.gettempdir()) / "model-training-runtime" / "workspaces",
            )
        )
    ).resolve()
    settings = RuntimeExecutionSettings(
        workspace_root=workspace_root,
        idle_timeout_seconds=int(execution_config.get("idle_timeout_seconds", 180)),
        max_output_bytes=int(execution_config.get("max_output_bytes", 2 * 1024 * 1024)),
        max_processes=int(execution_config.get("max_processes", 32)),
        process_fsize_bytes=int(execution_config.get("process_fsize_bytes", 50 * 1024 * 1024)),
        process_nofile=int(execution_config.get("process_nofile", 512)),
    )
    runtimes = [
        ManagedRuntimeSpec(runtime_id=runtime_id.strip(), python_executable=python_executable)
        for runtime_id in runtime_ids
    ]
    coordinator = ExecutionCoordinator(
        OpenDalS3Storage(),
        TrainingRuntimeManager(settings, runtimes),
        executor=ServiceSubprocessExecutor(),
    )
    return coordinator, workspace_root


@app.post("/v1/executions/run", response_model=DirectExecutionResponse)
async def run_training_execution(
    submission: TrainingCodeSubmission,
    _: None = Depends(require_registration_authorization),
) -> DirectExecutionResponse:
    """Run one registered training package directly inside this service.

    This synchronous HTTP path is intentionally diagnostic. It exercises the
    same coordinator, runner, S3 snapshot materialization, and result protocol
    used by the service-owned MQ consumer.
    """
    config = load_model_training_runtime_config()
    try:
        validate_execution_policy(submission, config)
    except ExecutionPolicyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    coordinator, workspace_root = get_training_coordinator()
    try:
        outcome = await coordinator.execute(submission)
        try:
            persisted = await persist_execution_artifacts(coordinator.storage, outcome)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "training result artifacts could not be persisted",
                    "error_type": exc.__class__.__name__,
                },
            ) from exc
        return DirectExecutionResponse(
            execution_id=str(outcome.execution.execution_id),
            result=outcome.result,
            events=list(outcome.events),
            logs=list(outcome.logs),
            artifacts=[_persisted_artifact_payload(item) for item in persisted],
        )
    except ExecutionCoordinatorError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": str(exc), "error_detail": exc.error_detail},
        ) from exc
    finally:
        shutil.rmtree(workspace_root / str(submission.execution_id), ignore_errors=True)


def _persisted_artifact_payload(item: PersistedArtifact) -> dict[str, Any]:
    return {
        "artifact": item.artifact.model_dump(mode="json"),
        "object": item.object.model_dump(mode="json"),
    }


@app.post("/v1/registrations/packages")
async def register_package(
    archive: bytes = Body(media_type="application/zip"),
    archive_name: str = "training-package.zip",
    _: None = Depends(require_registration_authorization),
) -> dict[str, Any]:
    """Store a validated code package as an immutable S3-backed release.

    This endpoint does not enable the package, create a training task, or run
    submitted code. It is intended for platform-admin workflow integration.
    """
    try:
        outcome = await get_package_registry().register_package(
            archive_name=archive_name,
            archive_bytes=archive,
        )
    except (PackageArchiveValidationError, PackageRegistryError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "created": outcome.created,
        "registration": outcome.registration.model_dump(mode="json"),
    }


@app.post("/v1/registrations/model-packages")
async def register_model_package(
    archive: bytes = Body(media_type="application/zip"),
    archive_name: str = "training-model-package.zip",
    _: None = Depends(require_registration_authorization),
) -> dict[str, Any]:
    """Import a manifest-declared base-model ZIP into immutable models objects."""
    try:
        outcome = await get_package_registry().register_model_package(
            archive_name=archive_name,
            archive_bytes=archive,
        )
    except (PackageArchiveValidationError, PackageRegistryError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "created": outcome.created,
        "registration": outcome.registration.model_dump(mode="json"),
    }


@app.post("/v1/registrations/dataset-snapshots")
async def register_dataset_snapshot(
    manifest: TrainingDatasetSourceManifest,
    _: None = Depends(require_registration_authorization),
) -> dict[str, Any]:
    """Persist a resolved existing-platform S3 source list by digest."""
    try:
        registration = await get_package_registry().register_dataset_snapshot(manifest)
    except PackageRegistryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "created": registration.created,
        "registration": {
            "source_manifest": registration.source_manifest.model_dump(mode="json"),
            "object": registration.object.model_dump(mode="json"),
        },
    }


def _ensure_admitted(action) -> None:
    try:
        action()
    except ContractAdmissionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
