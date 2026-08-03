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
DATASET_SOURCE_PROTOCOL_VERSION = "training-dataset-source-manifest/v1"
MODEL_PACKAGE_PROTOCOL_VERSION = "training-model-package/v1"
EXECUTION_PROTOCOL_VERSION = "training-execution/v1"
EVENT_PROTOCOL_VERSION = "training-event/v1"
RESULT_PROTOCOL_VERSION = "training-result/v1"
SUBMISSION_PROTOCOL_VERSION = "training-code-submit/v1"

PACKAGE_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,127}$")
TASK_KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
FRAMEWORK_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
FORMAT_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
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


def _path_is_same_or_descendant(path: PurePosixPath, parent: PurePosixPath) -> bool:
    return path == parent or parent in path.parents


def _finite_metric_values(value: dict[str, float]) -> dict[str, float]:
    for name, metric in value.items():
        if not name.strip():
            raise ValueError("metric names must not be empty")
        if not math.isfinite(metric):
            raise ValueError(f"metric `{name}` must be finite")
    return value


def _non_empty_unique_strings(value: list[str], field_name: str) -> list[str]:
    normalized = [item.strip() for item in value]
    if any(not item for item in normalized):
        raise ValueError(f"{field_name} must not contain empty values")
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ArtifactRole(str, Enum):
    MODEL = "model"
    CHECKPOINT = "checkpoint"
    REPORT = "report"
    LOG = "log"
    OTHER = "other"


class StorageBucket(str, Enum):
    """Logical buckets already provisioned by the platform's S3 configuration."""

    DEFAULT = "default"
    DATASETS = "datasets"
    MODELS = "models"
    ANNOTATIONS = "annotations"


class TrainingDataInputMode(str, Enum):
    """The platform-approved source from which a package receives training data."""

    PLATFORM_DATASET = "platform_dataset"
    SCRIPT_MANAGED = "script_managed"


class S3ObjectReference(ContractModel):
    """A platform-owned OpenDAL/S3 object, never an arbitrary URL or path."""

    bucket: StorageBucket
    object_key: str
    sha256: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)

    _validate_object_key = field_validator("object_key")(_relative_path)

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str | None) -> str | None:
        if value is not None and not SHA256_PATTERN.fullmatch(value):
            raise ValueError("must be a lowercase SHA-256 hex digest")
        return value


class PackageRuntime(ContractModel):
    """A runtime must be selected from platform-managed, immutable images."""

    id: str = Field(min_length=1, max_length=128)
    kind: Literal["platform_managed"] = "platform_managed"


class ModelFramework(ContractModel):
    """Exact framework compatibility identity for a serialized model artifact."""

    id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=128)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not FRAMEWORK_ID_PATTERN.fullmatch(normalized):
            raise ValueError("must contain lowercase letters, digits, '_', '-' or '.' only")
        return normalized

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized


class ModelInputMode(str, Enum):
    INITIALIZE = "initialize"
    RESUME = "resume"


class ModelInputContract(ContractModel):
    """How this package may consume a platform-stored base model/checkpoint."""

    required: bool = False
    framework: ModelFramework
    formats: list[str] = Field(min_length=1, max_length=16)
    modes: list[ModelInputMode] = Field(min_length=1, max_length=2)
    require_matching_task_kind: bool = True
    require_matching_class_names_for_resume: bool = True

    @field_validator("formats")
    @classmethod
    def normalize_formats(cls, value: list[str]) -> list[str]:
        normalized = [item.strip().lower() for item in value if item.strip()]
        if not normalized:
            raise ValueError("must contain at least one non-empty format")
        if len(normalized) != len(set(normalized)):
            raise ValueError("must not contain duplicate formats")
        return normalized

    @field_validator("modes")
    @classmethod
    def reject_duplicate_modes(cls, value: list[ModelInputMode]) -> list[ModelInputMode]:
        if len(value) != len(set(value)):
            raise ValueError("must not contain duplicate modes")
        return value


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

    @field_validator("data_modalities", "annotation_kinds")
    @classmethod
    def validate_kinds(cls, value: list[str], info) -> list[str]:
        return _non_empty_unique_strings(value, info.field_name)


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
        if len(normalized) != len(set(normalized)):
            raise ValueError("must not contain duplicate formats")
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
    input_modes: list[TrainingDataInputMode] = Field(
        default_factory=lambda: [TrainingDataInputMode.PLATFORM_DATASET],
        min_length=1,
        max_length=2,
    )
    parameters_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object", "properties": {}})
    model_input_contract: ModelInputContract | None = None
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

    @field_validator("input_modes")
    @classmethod
    def reject_duplicate_input_modes(cls, value: list[TrainingDataInputMode]) -> list[TrainingDataInputMode]:
        if len(value) != len(set(value)):
            raise ValueError("must not contain duplicate input modes")
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


class DatasetSourceItem(ContractModel):
    """One S3-backed sample before the worker materializes local input files."""

    item_id: str = Field(min_length=1, max_length=256)
    split: Literal["train", "val", "test", "unspecified"] = "unspecified"
    media: S3ObjectReference
    annotation: S3ObjectReference | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def restrict_media_to_dataset_bucket(self) -> "DatasetSourceItem":
        if self.media.bucket != StorageBucket.DATASETS:
            raise ValueError("media must reference the datasets bucket")
        if self.annotation is not None and self.annotation.bucket != StorageBucket.ANNOTATIONS:
            raise ValueError("annotation must reference the annotations bucket")
        return self


class TrainingDatasetSourceManifest(ContractModel):
    """S3-source manifest built from the platform's existing dataset records."""

    protocol_version: Literal[DATASET_SOURCE_PROTOCOL_VERSION]
    task_kind: str = Field(min_length=1, max_length=64)
    data_modalities: list[str] = Field(min_length=1, max_length=8)
    annotation_kinds: list[str] = Field(default_factory=list, max_length=16)
    class_names: list[str] = Field(default_factory=list, max_length=10000)
    items: list[DatasetSourceItem] = Field(min_length=1, max_length=10_000_000)

    @field_validator("task_kind")
    @classmethod
    def validate_task_kind(cls, value: str) -> str:
        if not TASK_KIND_PATTERN.fullmatch(value):
            raise ValueError("must contain lowercase letters, digits, and underscores only")
        return value

    @field_validator("data_modalities", "annotation_kinds", "class_names")
    @classmethod
    def validate_list_values(cls, value: list[str], info) -> list[str]:
        return _non_empty_unique_strings(value, info.field_name)

    @model_validator(mode="after")
    def reject_duplicate_item_ids(self) -> "TrainingDatasetSourceManifest":
        item_ids = [item.item_id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("items must not contain duplicate item_id values")
        return self


class TrainingDatasetManifest(ContractModel):
    """Materialized input manifest made by the orchestrator, never by package code."""

    protocol_version: Literal[DATASET_PROTOCOL_VERSION]
    task_kind: str = Field(min_length=1, max_length=64)
    data_modalities: list[str] = Field(min_length=1, max_length=8)
    annotation_kinds: list[str] = Field(default_factory=list, max_length=16)
    class_names: list[str] = Field(default_factory=list, max_length=10000)
    items: list[DatasetItem] = Field(default_factory=list, max_length=10_000_000)

    @field_validator("task_kind")
    @classmethod
    def validate_task_kind(cls, value: str) -> str:
        if not TASK_KIND_PATTERN.fullmatch(value):
            raise ValueError("must contain lowercase letters, digits, and underscores only")
        return value

    @field_validator("data_modalities", "annotation_kinds", "class_names")
    @classmethod
    def validate_list_values(cls, value: list[str], info) -> list[str]:
        return _non_empty_unique_strings(value, info.field_name)

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
    device: Literal["cpu", "cuda"] = "cpu"
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


class ModelArtifactReference(ContractModel):
    """Immutable model/checkpoint artifact from the existing models bucket."""

    source: Literal["uploaded_model_package", "registered_model", "previous_execution"]
    object: S3ObjectReference
    format: str = Field(min_length=1, max_length=64)
    task_kind: str = Field(min_length=1, max_length=64)
    class_names: list[str] = Field(default_factory=list, max_length=10000)
    display_name: str = Field(min_length=1, max_length=255)
    framework: ModelFramework | None = None
    resume_supported: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("format")
    @classmethod
    def normalize_format(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not FORMAT_PATTERN.fullmatch(normalized):
            raise ValueError("must contain lowercase letters, digits, '_' or '-' only")
        return normalized

    @field_validator("task_kind")
    @classmethod
    def validate_task_kind(cls, value: str) -> str:
        if not TASK_KIND_PATTERN.fullmatch(value):
            raise ValueError("must contain lowercase letters, digits, and underscores only")
        return value

    @field_validator("class_names")
    @classmethod
    def validate_class_names(cls, value: list[str]) -> list[str]:
        return _non_empty_unique_strings(value, "class_names")

    @model_validator(mode="after")
    def require_models_bucket_and_digest(self) -> "ModelArtifactReference":
        if self.object.bucket != StorageBucket.MODELS:
            raise ValueError("model artifact must reference the models bucket")
        if self.object.sha256 is None or self.object.size_bytes is None:
            raise ValueError("model artifact must include immutable object SHA-256 and size_bytes")
        return self


class ModelInputReference(ContractModel):
    """Selected base model/checkpoint and the requested initialize/resume mode."""

    artifact: ModelArtifactReference
    mode: ModelInputMode


class TrainingModelPackageManifest(ContractModel):
    """Root `training_model_package.json` for an imported model/checkpoint ZIP."""

    protocol_version: Literal[MODEL_PACKAGE_PROTOCOL_VERSION]
    name: str = Field(min_length=1, max_length=255)
    task_kind: str = Field(min_length=1, max_length=64)
    class_names: list[str] = Field(default_factory=list, max_length=10000)
    framework: ModelFramework
    artifact_path: str
    format: str = Field(min_length=1, max_length=64)
    resume_checkpoint_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("task_kind")
    @classmethod
    def validate_task_kind(cls, value: str) -> str:
        if not TASK_KIND_PATTERN.fullmatch(value):
            raise ValueError("must contain lowercase letters, digits, and underscores only")
        return value

    @field_validator("class_names")
    @classmethod
    def validate_class_names(cls, value: list[str]) -> list[str]:
        return _non_empty_unique_strings(value, "class_names")

    _validate_artifact_path = field_validator("artifact_path")(_relative_path)

    @field_validator("resume_checkpoint_path")
    @classmethod
    def validate_resume_checkpoint_path(cls, value: str | None) -> str | None:
        return _relative_path(value) if value is not None else None

    @field_validator("format")
    @classmethod
    def normalize_format(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not FORMAT_PATTERN.fullmatch(normalized):
            raise ValueError("must contain lowercase letters, digits, '_' or '-' only")
        return normalized


class ModelPackageRegistration(ContractModel):
    """Immutable imported ZIP and the materializable artifacts it contains."""

    manifest: TrainingModelPackageManifest
    archive: S3ObjectReference
    package_file_name: str = Field(min_length=1, max_length=255)
    initialize_artifact: ModelArtifactReference
    resume_artifact: ModelArtifactReference | None = None

    @model_validator(mode="after")
    def registration_must_match_model_package(self) -> "ModelPackageRegistration":
        if (
            self.archive.bucket != StorageBucket.MODELS
            or self.archive.sha256 is None
            or self.archive.size_bytes is None
        ):
            raise ValueError("model package archive must be an immutable models bucket object")
        if self.initialize_artifact.source != "uploaded_model_package":
            raise ValueError("initialize_artifact must originate from the uploaded model package")
        if self.initialize_artifact.resume_supported:
            raise ValueError("initialize_artifact must not be marked resume_supported")
        if self.resume_artifact is None and self.manifest.resume_checkpoint_path is not None:
            raise ValueError("resume_checkpoint_path requires resume_artifact")
        if self.resume_artifact is not None:
            if self.manifest.resume_checkpoint_path is None:
                raise ValueError("resume_artifact requires manifest.resume_checkpoint_path")
            if not self.resume_artifact.resume_supported:
                raise ValueError("resume_artifact must be marked resume_supported")
        expected = (self.manifest.task_kind, self.manifest.class_names, self.manifest.framework)
        for artifact in (self.initialize_artifact, self.resume_artifact):
            if artifact is not None and (artifact.task_kind, artifact.class_names, artifact.framework) != expected:
                raise ValueError("model package artifacts must match the manifest task, classes, and framework")
        return self


class TrainingPackageRegistration(ContractModel):
    """Immutable code-package release stored in the default S3 bucket."""

    manifest: TrainingPackageManifest
    archive: S3ObjectReference
    package_file_name: str = Field(min_length=1, max_length=255)

    @model_validator(mode="after")
    def archive_must_match_manifest(self) -> "TrainingPackageRegistration":
        if self.archive.bucket != StorageBucket.DEFAULT:
            raise ValueError("package archive must reference the default package bucket")
        if self.archive.sha256 is None or self.archive.size_bytes is None:
            raise ValueError("package archive must include immutable SHA-256 and size_bytes")
        return self


class TrainingExecutionRequest(ContractModel):
    """Private JSON file passed to `train(context, report)` by the runtime."""

    protocol_version: Literal[EXECUTION_PROTOCOL_VERSION]
    execution_id: UUID
    task: TaskReference
    package: ResolvedPackage
    runtime: PackageRuntime
    workspace: ExecutionWorkspace
    dataset: TrainingDatasetManifest
    input_mode: TrainingDataInputMode = TrainingDataInputMode.PLATFORM_DATASET
    parameters: dict[str, Any] = Field(default_factory=dict)
    resources: ResourceAllocation
    model_input: ModelInputReference | None = None
    model_input_path: str | None = None
    package_manifest: TrainingPackageManifest | None = None

    @model_validator(mode="after")
    def package_and_dataset_must_match_task(self) -> "TrainingExecutionRequest":
        if self.dataset.task_kind != self.task.task_kind:
            raise ValueError("dataset.task_kind must match task.task_kind")
        if self.model_input_path is not None:
            self.model_input_path = _workspace_path(self.model_input_path)
        if self.model_input is None and self.model_input_path is not None:
            raise ValueError("model_input_path requires model_input")
        if self.model_input is not None and self.model_input_path is None:
            raise ValueError("model_input requires its materialized model_input_path")
        if self.model_input_path and not _path_is_same_or_descendant(
            PurePosixPath(self.model_input_path),
            PurePosixPath(self.workspace.input_dir),
        ):
            raise ValueError("model_input_path must be under workspace.input_dir")
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
    framework: ModelFramework
    resume_checkpoint_path: str | None = None
    preprocessing: dict[str, Any] = Field(default_factory=dict)
    postprocessing: dict[str, Any] = Field(default_factory=dict)

    @field_validator("task_kind")
    @classmethod
    def validate_task_kind(cls, value: str) -> str:
        if not TASK_KIND_PATTERN.fullmatch(value):
            raise ValueError("must contain lowercase letters, digits, and underscores only")
        return value

    @field_validator("class_names")
    @classmethod
    def validate_class_names(cls, value: list[str]) -> list[str]:
        return _non_empty_unique_strings(value, "class_names")

    @field_validator("resume_checkpoint_path")
    @classmethod
    def validate_resume_checkpoint_path(cls, value: str | None) -> str | None:
        return _relative_path(value) if value is not None else None


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


class TrainingCodeSubmission(ContractModel):
    """Immutable execution submission shared by HTTP now and MQ later."""

    protocol_version: Literal[SUBMISSION_PROTOCOL_VERSION]
    message_id: UUID
    execution_id: UUID
    task: TaskReference
    package: ResolvedPackage
    package_archive: S3ObjectReference
    input_mode: TrainingDataInputMode = TrainingDataInputMode.PLATFORM_DATASET
    dataset_source_snapshot: S3ObjectReference | None = None
    script_dataset: TrainingDatasetManifest | None = None
    runtime: PackageRuntime
    parameters: dict[str, Any] = Field(default_factory=dict)
    resources: ResourceAllocation
    model_input: ModelInputReference | None = None

    @model_validator(mode="after")
    def restrict_submission_object_buckets(self) -> "TrainingCodeSubmission":
        if self.package_archive.bucket != StorageBucket.DEFAULT:
            raise ValueError("package_archive must reference the default package bucket")
        if self.input_mode == TrainingDataInputMode.PLATFORM_DATASET:
            if self.dataset_source_snapshot is None:
                raise ValueError("platform_dataset input requires dataset_source_snapshot")
            if self.script_dataset is not None:
                raise ValueError("platform_dataset input must not include script_dataset")
            if self.dataset_source_snapshot.bucket != StorageBucket.DEFAULT:
                raise ValueError("dataset_source_snapshot must reference the default manifest bucket")
        else:
            if self.script_dataset is None:
                raise ValueError("script_managed input requires script_dataset")
            if self.dataset_source_snapshot is not None:
                raise ValueError("script_managed input must not include dataset_source_snapshot")
            if self.script_dataset.task_kind != self.task.task_kind:
                raise ValueError("script_dataset.task_kind must match task.task_kind")
            if self.script_dataset.items:
                raise ValueError("script_managed dataset must not contain platform materialized items")
        references = [("package_archive", self.package_archive)]
        if self.dataset_source_snapshot is not None:
            references.append(("dataset_source_snapshot", self.dataset_source_snapshot))
        for label, reference in references:
            if reference.sha256 is None or reference.size_bytes is None:
                raise ValueError(f"{label} must include immutable SHA-256 and size_bytes")
        return self
