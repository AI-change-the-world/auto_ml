"""Control-plane schemas for custom training packages and model packages."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RuntimeObjectReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bucket: Literal["default", "models"]
    object_key: str = Field(min_length=1, max_length=512)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class RuntimeFrameworkReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=128)


class RuntimeCodePackageManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: Literal["training-code-package/v1"]
    key: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,127}$")
    version: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    runtime: dict[str, Any]
    entrypoint: str = Field(min_length=1, max_length=512)
    entrypoint_symbol: Literal["train"] = "train"
    supported_tasks: list[dict[str, Any]] = Field(min_length=1, max_length=32)
    input_modes: list[Literal["platform_dataset", "script_managed"]] = Field(
        default_factory=lambda: ["platform_dataset"],
        min_length=1,
        max_length=2,
    )
    class_names: list[str] = Field(default_factory=list, max_length=10000)
    parameters_schema: dict[str, Any]
    model_input_contract: dict[str, Any] | None = None
    output_contract: dict[str, Any]


class RuntimeCodePackageRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: RuntimeCodePackageManifest
    archive: RuntimeObjectReference
    package_file_name: str = Field(min_length=1, max_length=255)


class RuntimeModelArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["uploaded_model_package"]
    object: RuntimeObjectReference
    format: str = Field(min_length=1, max_length=64)
    task_kind: str = Field(min_length=1, max_length=64)
    class_names: list[str] = Field(default_factory=list, max_length=10000)
    display_name: str = Field(min_length=1, max_length=255)
    framework: RuntimeFrameworkReference
    resume_supported: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuntimeModelPackageManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: Literal["training-model-package/v1"]
    name: str = Field(min_length=1, max_length=255)
    task_kind: str = Field(min_length=1, max_length=64)
    class_names: list[str] = Field(default_factory=list, max_length=10000)
    framework: RuntimeFrameworkReference
    artifact_path: str = Field(min_length=1, max_length=512)
    format: str = Field(min_length=1, max_length=64)
    resume_checkpoint_path: str | None = Field(default=None, max_length=512)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuntimeModelPackageRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: RuntimeModelPackageManifest
    archive: RuntimeObjectReference
    package_file_name: str = Field(min_length=1, max_length=255)
    initialize_artifact: RuntimeModelArtifact
    resume_artifact: RuntimeModelArtifact | None = None


class RuntimeCodePackageRegistrationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created: bool
    registration: RuntimeCodePackageRegistration


class RuntimeModelPackageRegistrationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created: bool
    registration: RuntimeModelPackageRegistration


class TrainingRuntimeCodePackageResponse(BaseModel):
    id: int
    package_key: str
    version: str
    name: str
    description: str | None = None
    runtime_id: str
    entrypoint: str
    package_sha256: str
    package_size_bytes: int
    package_file_name: str
    supported_tasks: list[dict[str, Any]]
    input_modes: list[Literal["platform_dataset", "script_managed"]]
    class_names: list[str]
    parameters_schema: dict[str, Any]
    model_input_contract: dict[str, Any] | None = None
    output_contract: dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class TrainingRuntimeModelPackageResponse(BaseModel):
    id: int
    name: str
    package_sha256: str
    package_size_bytes: int
    package_file_name: str
    task_kind: str
    class_names: list[str]
    framework_id: str
    framework_version: str
    artifact_format: str
    initialize_sha256: str
    initialize_size_bytes: int
    has_resume_checkpoint: bool
    metadata: dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime


class TrainingRuntimeCodePackageImportResponse(BaseModel):
    package: TrainingRuntimeCodePackageResponse
    registration_created: bool
    catalog_created: bool


class TrainingRuntimeModelPackageImportResponse(BaseModel):
    package: TrainingRuntimeModelPackageResponse
    registration_created: bool
    catalog_created: bool
