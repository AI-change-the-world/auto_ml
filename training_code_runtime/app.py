"""HTTP contract validation service for the exploratory training-code runtime."""
from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from contracts import (
    DATASET_PROTOCOL_VERSION,
    EVENT_PROTOCOL_VERSION,
    EXECUTION_PROTOCOL_VERSION,
    PACKAGE_PROTOCOL_VERSION,
    RESULT_PROTOCOL_VERSION,
    SUBMISSION_PROTOCOL_VERSION,
    TrainingCodeSubmission,
    TrainingDatasetManifest,
    TrainingExecutionRequest,
    TrainingEvent,
    TrainingPackageManifest,
    TrainingResult,
)
from package_validation import PackageArchiveValidationError, validate_package_archive


SERVICE_NAME = "training-code-runtime"
SERVICE_VERSION = "0.1.0-experimental"


class ValidationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool = True
    contract: str
    normalized: dict[str, Any]


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
            "execution": EXECUTION_PROTOCOL_VERSION,
            "event": EVENT_PROTOCOL_VERSION,
            "result": RESULT_PROTOCOL_VERSION,
            "mq_submission": SUBMISSION_PROTOCOL_VERSION,
        },
    }


@app.post("/v1/contracts/package/validate", response_model=ValidationResponse)
async def validate_package(manifest: TrainingPackageManifest) -> ValidationResponse:
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


@app.post("/v1/contracts/dataset-manifest/validate", response_model=ValidationResponse)
async def validate_dataset_manifest(manifest: TrainingDatasetManifest) -> ValidationResponse:
    return validated_response(DATASET_PROTOCOL_VERSION, manifest)


@app.post("/v1/contracts/execution/validate", response_model=ValidationResponse)
async def validate_execution(request: TrainingExecutionRequest) -> ValidationResponse:
    return validated_response(EXECUTION_PROTOCOL_VERSION, request)


@app.post("/v1/contracts/event/validate", response_model=ValidationResponse)
async def validate_event(event: TrainingEvent) -> ValidationResponse:
    return validated_response(EVENT_PROTOCOL_VERSION, event)


@app.post("/v1/contracts/result/validate", response_model=ValidationResponse)
async def validate_result(result: TrainingResult) -> ValidationResponse:
    return validated_response(RESULT_PROTOCOL_VERSION, result)


@app.post("/v1/contracts/mq-submission/validate", response_model=ValidationResponse)
async def validate_mq_submission(submission: TrainingCodeSubmission) -> ValidationResponse:
    return validated_response(SUBMISSION_PROTOCOL_VERSION, submission)
