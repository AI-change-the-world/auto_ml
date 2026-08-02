"""Versioned contracts for the exploratory training-code runtime.

This module intentionally contains no task scheduling, storage, or user-code
execution. It is the compatibility boundary that those later capabilities must
implement.
"""
from __future__ import annotations

import math
import re
from datetime import datetime
from enum import Enum
from pathlib import PurePosixPath
from typing import Annotated, Any, Literal, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator


PACKAGE_PROTOCOL_VERSION = "training-code-package/v1"
DATASET_PROTOCOL_VERSION = "training-dataset-manifest/v1"
EXECUTION_PROTOCOL_VERSION = "training-execution/v1"
EVENT_PROTOCOL_VERSION = "training-event/v1"
RESULT_PROTOCOL_VERSION = "training-result/v1"
SUBMISSION_PROTOCOL_VERSION = "training-code-submit/v1"

PACKAGE_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,127}$")
TASK_KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def _relative_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts or normalized == ".":
        raise ValueError("must be a non-empty relative POSIX path without '..'")
    return normalized


def _workspace_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if not path.is_absolute() or path != PurePosixPath("/workspace") and PurePosixPath("/workspace") not in path.parents:
        raise ValueError("must be an absolute path under /workspace")
    return normalized


def _finite_metric_values(value: dict[str, float]) -> dict[str, float]:
    for name, metric in value.items():
        if not name.strip():
            raise ValueError("metric names must not be empty")
        if not math.isfinite(metric):
            raise ValueError(f"metric `{name}` must be finite")
    return value


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ArtifactRole(str, Enum):
    MODEL = "model"
    CHECKPOINT = "checkpoint"
    REPORT = "report"
    LOG = "log"
    OTHER = "other"


class PackageRuntime(ContractModel):
    """A runtime must be selected from platform-managed, immutable images."""

    id: str = Field(min_length=1, max_length=128)
    kind: Literal["platform_managed"] = "platform_managed"


class SupportedTask(ContractModel):
    task_kind: str = Field(min_length=1, max_length=64)
    data_modalities: list[str] = Field(min_length=1, max_length=8)
    annotation_kinds: list[str] = Field(default_factory=list, max_length=16)

    @field_validator("task_kind")
    @classmethod
    def validate_task_kind(cls, value: str) -> str:
        if not TASK_KIND_PATTERN.fullmatch(value):
            raise ValueError("must contain lowercase letters, digits, and underscores only")
        return value


class ArtifactDeclaration(ContractModel):
    role: ArtifactRole
    formats: list[str] = Field(min_length=1, max_length=16)
    required: bool = True
    deployable: bool = False

    @field_validator("formats")
    @classmethod
    def normalize_formats(cls, value: list[str]) -> list[str]:
        normalized = [item.strip().lower() for item in value if item.strip()]
        if not normalized:
            raise ValueError("must contain at least one non-empty format")
        return normalized

    @model_validator(mode="after")
    def deployable_artifact_must_be_a_model(self) -> "ArtifactDeclaration":
        if self.deployable and self.role != ArtifactRole.MODEL:
            raise ValueError("only a model artifact may be deployable")
        return self


class PackageOutputContract(ContractModel):
    artifacts: list[ArtifactDeclaration] = Field(min_length=1, max_length=16)
    requires_model_metadata: bool = True

    @model_validator(mode="after")
    def reject_duplicate_artifact_declarations(self) -> "PackageOutputContract":
        keys = [(artifact.role.value, artifact.deployable) for artifact in self.artifacts]
        if len(keys) != len(set(keys)):
            raise ValueError("artifact declarations must not repeat the same role and deployable flag")
        return self


class TrainingPackageManifest(ContractModel):
    """`training_package.json` found at the root of an uploaded code package."""

    protocol_version: Literal[PACKAGE_PROTOCOL_VERSION]
    key: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    runtime: PackageRuntime
    entrypoint: str
    entrypoint_symbol: Literal["train"] = "train"
    supported_tasks: list[SupportedTask] = Field(min_length=1, max_length=32)
    parameters_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object", "properties": {}})
    output_contract: PackageOutputContract

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        if not PACKAGE_KEY_PATTERN.fullmatch(value):
            raise ValueError("must start with a lowercase letter and contain only lowercase letters, digits, '_' or '-'")
        return value

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if not SEMVER_PATTERN.fullmatch(value):
            raise ValueError("must be a semantic version, such as 1.0.0")
        return value

    @field_validator("entrypoint")
    @classmethod
    def validate_entrypoint(cls, value: str) -> str:
        value = _relative_path(value)
        if not value.endswith(".py"):
            raise ValueError("must reference a Python file")
        return value

    @field_validator("parameters_schema")
    @classmethod
    def validate_parameters_schema(cls, value: dict[str, Any]) -> dict[str, Any]:
        if value.get("type") != "object":
            raise ValueError("must be a JSON Schema object with root type 'object'")
        if not isinstance(value.get("properties", {}), dict):
            raise ValueError("properties must be an object when provided")
        return value


class DatasetItem(ContractModel):
    item_id: str = Field(min_length=1, max_length=256)
    split: Literal["train", "val", "test", "unspecified"] = "unspecified"
    media_path: str
    annotation_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    _validate_media_path = field_validator("media_path")(_relative_path)

    @field_validator("annotation_path")
    @classmethod
    def validate_annotation_path(cls, value: str | None) -> str | None:
        return _relative_path(value) if value is not None else None


class TrainingDatasetManifest(ContractModel):
    """Materialized input manifest made by the orchestrator, never by package code."""

    protocol_version: Literal[DATASET_PROTOCOL_VERSION]
    task_kind: str = Field(min_length=1, max_length=64)
    data_modalities: list[str] = Field(min_length=1, max_length=8)
    annotation_kinds: list[str] = Field(default_factory=list, max_length=16)
    class_names: list[str] = Field(default_factory=list, max_length=10000)
    items: list[DatasetItem] = Field(min_length=1, max_length=10_000_000)

    @field_validator("task_kind")
    @classmethod
    def validate_task_kind(cls, value: str) -> str:
        if not TASK_KIND_PATTERN.fullmatch(value):
            raise ValueError("must contain lowercase letters, digits, and underscores only")
        return value

    @model_validator(mode="after")
    def reject_duplicate_item_ids(self) -> "TrainingDatasetManifest":
        item_ids = [item.item_id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("items must not contain duplicate item_id values")
        return self


class TaskReference(ContractModel):
    task_id: int = Field(gt=0)
    task_kind: str = Field(min_length=1, max_length=64)

    @field_validator("task_kind")
    @classmethod
    def validate_task_kind(cls, value: str) -> str:
        if not TASK_KIND_PATTERN.fullmatch(value):
            raise ValueError("must contain lowercase letters, digits, and underscores only")
        return value


class ResolvedPackage(ContractModel):
    key: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    sha256: str

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        if not PACKAGE_KEY_PATTERN.fullmatch(value):
            raise ValueError("must be a valid package key")
        return value

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if not SEMVER_PATTERN.fullmatch(value):
            raise ValueError("must be a semantic version")
        return value

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        if not SHA256_PATTERN.fullmatch(value):
            raise ValueError("must be a lowercase SHA-256 hex digest")
        return value


class ExecutionWorkspace(ContractModel):
    root_dir: str
    code_dir: str
    input_dir: str
    output_dir: str
    dataset_manifest_path: str

    _validate_root_dir = field_validator("root_dir")(_workspace_path)
    _validate_code_dir = field_validator("code_dir")(_workspace_path)
    _validate_input_dir = field_validator("input_dir")(_workspace_path)
    _validate_output_dir = field_validator("output_dir")(_workspace_path)
    _validate_dataset_manifest_path = field_validator("dataset_manifest_path")(_workspace_path)


class ResourceAllocation(ContractModel):
    device: Literal["cpu", "cuda", "mps"] = "cpu"
    gpu_count: int = Field(default=0, ge=0, le=64)
    cpu_cores: float = Field(default=1, gt=0, le=256)
    memory_bytes: int = Field(default=1024 * 1024 * 1024, gt=0)
    timeout_seconds: int = Field(default=3600, gt=0, le=7 * 24 * 60 * 60)

    @model_validator(mode="after")
    def ensure_gpu_matches_device(self) -> "ResourceAllocation":
        if self.device == "cuda" and self.gpu_count < 1:
            raise ValueError("cuda execution requires gpu_count to be at least 1")
        if self.device != "cuda" and self.gpu_count:
            raise ValueError("gpu_count must be 0 unless device is cuda")
        return self


class ResumeInput(ContractModel):
    checkpoint_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    _validate_checkpoint_path = field_validator("checkpoint_path")(_workspace_path)


class TrainingExecutionRequest(ContractModel):
    """Private JSON file passed to `train(context, report)` by the runtime."""

    protocol_version: Literal[EXECUTION_PROTOCOL_VERSION]
    execution_id: UUID
    task: TaskReference
    package: ResolvedPackage
    runtime: PackageRuntime
    workspace: ExecutionWorkspace
    dataset: TrainingDatasetManifest
    parameters: dict[str, Any] = Field(default_factory=dict)
    resources: ResourceAllocation
    resume: ResumeInput | None = None

    @model_validator(mode="after")
    def package_and_dataset_must_match_task(self) -> "TrainingExecutionRequest":
        if self.dataset.task_kind != self.task.task_kind:
            raise ValueError("dataset.task_kind must match task.task_kind")
        return self


class TrainingError(ContractModel):
    stage: str = Field(min_length=1, max_length=128)
    error_type: str = Field(min_length=1, max_length=256)
    message: str = Field(min_length=1, max_length=8000)
    retryable: bool = False


class EventBase(ContractModel):
    protocol_version: Literal[EVENT_PROTOCOL_VERSION]
    execution_id: UUID
    sequence: int = Field(ge=0)
    occurred_at: datetime


class PhaseEvent(EventBase):
    event_type: Literal["phase"]
    phase: str = Field(min_length=1, max_length=128)
    message: str | None = Field(default=None, max_length=4000)


class LogEvent(EventBase):
    event_type: Literal["log"]
    level: Literal["debug", "info", "warning", "error"] = "info"
    message: str = Field(min_length=1, max_length=16000)


class MetricEvent(EventBase):
    event_type: Literal["metric"]
    split: Literal["train", "val", "test", "other"] = "train"
    epoch: int | None = Field(default=None, ge=0)
    step: int | None = Field(default=None, ge=0)
    metrics: dict[str, float] = Field(min_length=1, max_length=128)

    _validate_metrics = field_validator("metrics")(_finite_metric_values)


class CheckpointEvent(EventBase):
    event_type: Literal["checkpoint"]
    path: str
    message: str | None = Field(default=None, max_length=4000)

    _validate_path = field_validator("path")(_relative_path)


TrainingEvent = Annotated[
    Union[PhaseEvent, LogEvent, MetricEvent, CheckpointEvent],
    Field(discriminator="event_type"),
]
training_event_adapter = TypeAdapter(TrainingEvent)


class ArtifactResult(ContractModel):
    path: str
    role: ArtifactRole
    format: str = Field(min_length=1, max_length=64)
    size_bytes: int = Field(ge=0)
    sha256: str | None = None
    deployable: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    _validate_path = field_validator("path")(_relative_path)

    @field_validator("format")
    @classmethod
    def normalize_format(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str | None) -> str | None:
        if value is not None and not SHA256_PATTERN.fullmatch(value):
            raise ValueError("must be a lowercase SHA-256 hex digest")
        return value

    @model_validator(mode="after")
    def deployable_artifact_must_be_a_model(self) -> "ArtifactResult":
        if self.deployable and self.role != ArtifactRole.MODEL:
            raise ValueError("only a model artifact may be deployable")
        return self


class ProducedArtifact(ContractModel):
    """Artifact description returned by package code before the runner enriches it."""

    path: str
    role: ArtifactRole
    format: str = Field(min_length=1, max_length=64)
    deployable: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    _validate_path = field_validator("path")(_relative_path)

    @field_validator("format")
    @classmethod
    def normalize_format(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def deployable_artifact_must_be_a_model(self) -> "ProducedArtifact":
        if self.deployable and self.role != ArtifactRole.MODEL:
            raise ValueError("only a model artifact may be deployable")
        return self


class ModelMetadata(ContractModel):
    task_kind: str = Field(min_length=1, max_length=64)
    class_names: list[str] = Field(default_factory=list, max_length=10000)
    preprocessing: dict[str, Any] = Field(default_factory=dict)
    postprocessing: dict[str, Any] = Field(default_factory=dict)

    @field_validator("task_kind")
    @classmethod
    def validate_task_kind(cls, value: str) -> str:
        if not TASK_KIND_PATTERN.fullmatch(value):
            raise ValueError("must contain lowercase letters, digits, and underscores only")
        return value


class TrainingPackageCompletion(ContractModel):
    """Successful value returned from `train(context, report)` by package code."""

    summary: str | None = Field(default=None, max_length=8000)
    metrics: dict[str, float] = Field(default_factory=dict, max_length=128)
    artifacts: list[ProducedArtifact] = Field(default_factory=list, max_length=128)
    model: ModelMetadata | None = None

    _validate_metrics = field_validator("metrics")(_finite_metric_values)

    @model_validator(mode="after")
    def deployable_artifacts_require_model_metadata(self) -> "TrainingPackageCompletion":
        if any(artifact.deployable for artifact in self.artifacts) and self.model is None:
            raise ValueError("deployable artifacts require model metadata")
        return self


class TrainingResult(ContractModel):
    """`result.json` written under the runtime-owned output directory."""

    protocol_version: Literal[RESULT_PROTOCOL_VERSION]
    execution_id: UUID
    status: Literal["succeeded", "failed", "cancelled"]
    summary: str | None = Field(default=None, max_length=8000)
    metrics: dict[str, float] = Field(default_factory=dict, max_length=128)
    artifacts: list[ArtifactResult] = Field(default_factory=list, max_length=128)
    model: ModelMetadata | None = None
    error: TrainingError | None = None

    _validate_metrics = field_validator("metrics")(_finite_metric_values)

    @model_validator(mode="after")
    def validate_result_state(self) -> "TrainingResult":
        paths = [artifact.path for artifact in self.artifacts]
        if len(paths) != len(set(paths)):
            raise ValueError("artifacts must not repeat a path")
        deployable_artifacts = [artifact for artifact in self.artifacts if artifact.deployable]
        if deployable_artifacts and self.model is None:
            raise ValueError("deployable artifacts require model metadata")
        if self.status == "succeeded" and self.error is not None:
            raise ValueError("succeeded results must not contain error")
        if self.status in {"failed", "cancelled"} and self.error is None:
            raise ValueError("failed or cancelled results must contain error")
        return self


class ObjectReference(ContractModel):
    object_key: str
    sha256: str

    _validate_object_key = field_validator("object_key")(_relative_path)

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        if not SHA256_PATTERN.fullmatch(value):
            raise ValueError("must be a lowercase SHA-256 hex digest")
        return value


class TrainingCodeSubmission(ContractModel):
    """Future MQ payload; the worker creates local workspace paths after consuming it."""

    protocol_version: Literal[SUBMISSION_PROTOCOL_VERSION]
    message_id: UUID
    execution_id: UUID
    task: TaskReference
    package: ResolvedPackage
    package_archive: ObjectReference
    dataset_manifest: ObjectReference
    runtime: PackageRuntime
    parameters: dict[str, Any] = Field(default_factory=dict)
    resources: ResourceAllocation
    resume_artifact: ObjectReference | None = None
