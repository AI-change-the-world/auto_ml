"""HTTP contract validation service for the exploratory training-code runtime."""
from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from admission import (
    ContractAdmissionError,
    validate_execution_admission,
    validate_package_manifest,
    validate_result_admission,
)
from contracts import (
    DATASET_PROTOCOL_VERSION,
    DATASET_SOURCE_PROTOCOL_VERSION,
    EVENT_PROTOCOL_VERSION,
    EXECUTION_PROTOCOL_VERSION,
    PACKAGE_PROTOCOL_VERSION,
    RESULT_PROTOCOL_VERSION,
    SUBMISSION_PROTOCOL_VERSION,
    TrainingCodeSubmission,
    TrainingDatasetManifest,
    TrainingDatasetSourceManifest,
    TrainingExecutionRequest,
    TrainingEvent,
    TrainingPackageManifest,
    TrainingResult,
)
from package_validation import (
    PackageArchiveValidationError,
    validate_model_package_archive,
    validate_package_archive,
)
from registry import PackageRegistryError, TrainingPackageRegistry
from storage import OpenDalS3Storage


SERVICE_NAME = "training-code-runtime"
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


def validated_response(contract: str, value: Any) -> ValidationResponse:
    return ValidationResponse(
        contract=contract,
        normalized=value.model_dump(mode="json"),
    )


app = FastAPI(
    title="Training Code Runtime",
    description=(
        "Experimental contract service. It validates versioned training-code "
        "contracts only; it does not execute user code or consume training jobs."
    ),
    version=SERVICE_VERSION,
)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "mode": "contract_validation_only",
        "execution_enabled": False,
        "mq_consumer_enabled": False,
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
async def validate_event(event: TrainingEvent) -> ValidationResponse:
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


@app.post("/v1/registrations/packages")
async def register_package(
    archive: bytes = Body(media_type="application/zip"),
    archive_name: str = "training-package.zip",
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
async def register_dataset_snapshot(manifest: TrainingDatasetSourceManifest) -> dict[str, Any]:
    """Persist a resolved existing-platform S3 source list by digest."""
    try:
        registration = await get_package_registry().register_dataset_snapshot(manifest)
    except PackageRegistryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "created": True,
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
