"""任务 Schema"""
from datetime import datetime
from typing import Any, Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


class TaskSourceItem(BaseModel):
    dataset_id: int
    annotation_id: int


class TaskSourceResponse(BaseModel):
    id: int
    task_id: int
    dataset_id: int
    annotation_id: int
    source_order: int
    source_name: Optional[str] = None

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    task_type: int = Field(default=0, description="0=检测, 1=分类, 2=分割, 3=姿态")
    dataset_id: Optional[int] = None
    annotation_id: Optional[int] = None
    sources: Optional[List[TaskSourceItem]] = None
    config: Optional[str] = Field(default=None, description="配置 JSON")


class RuntimeTrainingResources(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device: Literal["cpu", "cuda"] = "cpu"
    gpu_count: int = Field(default=0, ge=0, le=64)
    cpu_cores: float = Field(default=1, gt=0, le=256)
    memory_bytes: int = Field(default=1024 * 1024 * 1024, gt=0)
    timeout_seconds: int = Field(default=3600, gt=0, le=7 * 24 * 60 * 60)

    @model_validator(mode="after")
    def validate_device(self) -> "RuntimeTrainingResources":
        if self.device == "cuda" and self.gpu_count < 1:
            raise ValueError("cuda execution requires gpu_count to be at least 1")
        if self.device != "cuda" and self.gpu_count:
            raise ValueError("gpu_count must be 0 unless device is cuda")
        return self


class RuntimeScriptTaskCreate(BaseModel):
    """Control-plane request that becomes one immutable training-code-submit/v1."""

    model_config = ConfigDict(extra="forbid")

    code_package_id: int = Field(gt=0)
    task_type: Literal[0, 1, 2] = Field(default=0)
    input_mode: Literal["platform_dataset", "script_managed"] = "platform_dataset"
    dataset_id: Optional[int] = Field(default=None, gt=0)
    annotation_id: Optional[int] = Field(default=None, gt=0)
    sources: Optional[List[TaskSourceItem]] = None
    class_names: List[str] = Field(default_factory=list, max_length=10000)
    data_modalities: List[str] = Field(default_factory=lambda: ["image"], min_length=1, max_length=8)
    annotation_kinds: List[str] = Field(default_factory=list, max_length=16)
    parameters: dict[str, Any] = Field(default_factory=dict)
    resources: RuntimeTrainingResources = Field(default_factory=RuntimeTrainingResources)
    model_package_id: Optional[int] = Field(default=None, gt=0)
    model_input_mode: Literal["initialize", "resume"] = "initialize"

    @model_validator(mode="after")
    def validate_selected_input_mode(self) -> "RuntimeScriptTaskCreate":
        has_direct_source = self.dataset_id is not None or self.annotation_id is not None
        if self.input_mode == "platform_dataset":
            if self.sources:
                if has_direct_source:
                    raise ValueError("sources cannot be combined with dataset_id or annotation_id")
                pairs = {(source.dataset_id, source.annotation_id) for source in self.sources}
                if len(pairs) != len(self.sources):
                    raise ValueError("sources must not repeat the same dataset and annotation")
            elif self.dataset_id is None or self.annotation_id is None:
                raise ValueError("platform_dataset requires dataset_id and annotation_id or sources")
        elif has_direct_source or self.sources:
            raise ValueError("script_managed input must not include datasets or annotations")
        if self.input_mode == "script_managed":
            normalized = [item.strip() for item in self.class_names]
            if normalized and (any(not item for item in normalized) or len(normalized) != len(set(normalized))):
                raise ValueError("script_managed class_names must contain unique non-empty values")
        if self.model_package_id is None and self.model_input_mode != "initialize":
            raise ValueError("model_input_mode=resume requires model_package_id")
        return self


class TrainingDatasetSnapshotSourceItem(BaseModel):
    """Exact source selector accepted by the experimental snapshot preview."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: int = Field(gt=0)
    annotation_id: int = Field(gt=0)


class TrainingDatasetSnapshotPreviewRequest(BaseModel):
    """Read-only source selection for the exploratory training runtime."""

    model_config = ConfigDict(extra="forbid")

    task_type: Literal[0, 1, 2] = Field(default=0, description="0=检测, 1=分类, 2=分割")
    dataset_id: Optional[int] = None
    annotation_id: Optional[int] = None
    sources: Optional[List[TrainingDatasetSnapshotSourceItem]] = None

    @model_validator(mode="after")
    def validate_source_selector(self) -> "TrainingDatasetSnapshotPreviewRequest":
        has_direct_source = self.dataset_id is not None or self.annotation_id is not None
        if self.sources is not None:
            if not self.sources:
                raise ValueError("sources must not be empty when provided")
            if has_direct_source:
                raise ValueError("sources cannot be combined with dataset_id or annotation_id")
            source_ids = {(item.dataset_id, item.annotation_id) for item in self.sources}
            if len(source_ids) != len(self.sources):
                raise ValueError("sources must not repeat the same dataset_id and annotation_id")
            return self
        if self.dataset_id is None or self.annotation_id is None:
            raise ValueError("dataset_id and annotation_id are required when sources is omitted")
        if self.dataset_id <= 0 or self.annotation_id <= 0:
            raise ValueError("dataset_id and annotation_id must be positive integers")
        return self


class TrainingDatasetSnapshotRegisterRequest(TrainingDatasetSnapshotPreviewRequest):
    """Explicit opt-in to pin a previewed source manifest through the runtime."""


class TrainingDatasetSnapshotMediaReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bucket: Literal["datasets"]
    object_key: str = Field(min_length=1)
    sha256: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    size_bytes: Optional[int] = Field(default=None, ge=0)


class TrainingDatasetSnapshotAnnotationReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bucket: Literal["annotations"]
    object_key: str = Field(min_length=1)
    sha256: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    size_bytes: Optional[int] = Field(default=None, ge=0)


class TrainingDatasetSnapshotItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(min_length=1, max_length=256)
    split: Literal["train", "val", "test", "unspecified"] = "unspecified"
    media: TrainingDatasetSnapshotMediaReference
    annotation: TrainingDatasetSnapshotAnnotationReference
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrainingDatasetSnapshotManifest(BaseModel):
    """Unpinned S3 source manifest returned by the read-only preview."""

    model_config = ConfigDict(extra="forbid")

    protocol_version: Literal["training-dataset-source-manifest/v1"]
    task_kind: Literal["detection", "classification", "segmentation"]
    data_modalities: List[Literal["image"]] = Field(min_length=1, max_length=1)
    annotation_kinds: List[Literal["detection", "classification", "segmentation"]] = Field(
        min_length=1,
        max_length=1,
    )
    class_names: List[str] = Field(min_length=1)
    items: List[TrainingDatasetSnapshotItem] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_task_shape(self) -> "TrainingDatasetSnapshotManifest":
        expected_annotation_kind = self.task_kind
        if self.data_modalities != ["image"]:
            raise ValueError("data_modalities must contain only image")
        if self.annotation_kinds != [expected_annotation_kind]:
            raise ValueError("annotation_kinds must match task_kind")
        if len(self.class_names) != len(set(self.class_names)) or any(not name.strip() for name in self.class_names):
            raise ValueError("class_names must contain unique non-empty values")
        item_ids = [item.item_id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("items must not contain duplicate item_id values")
        return self


class TrainingDatasetSnapshotPreviewResponse(BaseModel):
    """No S3 read/write or task dispatch happens while producing this preview."""

    manifest: TrainingDatasetSnapshotManifest
    source_count: int = Field(gt=0)
    sample_count: int = Field(gt=0)
    registration_enabled: bool = False


class TrainingDatasetSnapshotObjectReference(BaseModel):
    """Immutable source-manifest object written by the experimental runtime."""

    model_config = ConfigDict(extra="forbid")

    bucket: Literal["default"]
    object_key: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class TrainingDatasetSnapshotRegistrationResponse(BaseModel):
    """Pinned snapshot returned after the runtime has read and hashed every input."""

    manifest: TrainingDatasetSnapshotManifest
    object: TrainingDatasetSnapshotObjectReference
    created: bool
    source_count: int = Field(gt=0)
    sample_count: int = Field(gt=0)


class TaskResponse(BaseModel):
    id: int
    task_type: int
    dataset_id: Optional[int]
    annotation_id: Optional[int]
    status: int
    config: Optional[str]
    result: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_stale: bool = False
    stale_seconds: Optional[int] = None
    sources: List[TaskSourceResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TaskLogResponse(BaseModel):
    id: int
    task_id: int
    content: Optional[str]
    log_level: str
    created_at: datetime

    class Config:
        from_attributes = True


class BaseModelResponse(BaseModel):
    id: int
    name: str
    model_type: Optional[str]
    description: Optional[str]
    save_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingHistoryQuery(BaseModel):
    task_type: int = Field(default=0, description="0=检测, 1=分类, 2=分割, 3=姿态")
    sources: List[TaskSourceItem] = Field(default_factory=list)
    label_format: Optional[Literal["auto", "bbox", "obb"]] = None


class TrainingHistoryCandidateResponse(BaseModel):
    model_id: int
    task_id: int
    model_name: str
    model_path: Optional[str] = None
    model_type: Optional[str] = None
    base_model_name: Optional[str] = None
    dataset_id: Optional[int] = None
    annotation_id: Optional[int] = None
    source_count: int = 0
    created_at: datetime


class TrainingAugmentationConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    enabled: bool = True
    degrees: Optional[float] = Field(default=0.0, ge=0, le=180)
    translate: Optional[float] = Field(default=0.1, ge=0, le=1)
    scale: Optional[float] = Field(default=0.5, ge=0, le=1)
    shear: Optional[float] = Field(default=0.0, ge=0, le=180)
    perspective: Optional[float] = Field(default=0.0, ge=0, le=0.001)
    fliplr: Optional[float] = Field(default=0.5, ge=0, le=1)
    flipud: Optional[float] = Field(default=0.0, ge=0, le=1)
    hsv_h: Optional[float] = Field(default=0.015, ge=0, le=1)
    hsv_s: Optional[float] = Field(default=0.7, ge=0, le=1)
    hsv_v: Optional[float] = Field(default=0.4, ge=0, le=1)
    mosaic: Optional[float] = Field(default=1.0, ge=0, le=1)
    mixup: Optional[float] = Field(default=0.0, ge=0, le=1)
    copy_paste: Optional[float] = Field(default=0.0, ge=0, le=1)
    close_mosaic: Optional[int] = Field(default=10, ge=0, le=10000)
    auto_augment: Optional[Literal["randaugment", "autoaugment", "augmix", "none"]] = Field(
        default="randaugment",
        description="classification only",
    )
    erasing: Optional[float] = Field(default=0.4, ge=0, le=1)


class TrainingOptimizerConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    optimizer: Optional[str] = Field(default="auto", description="auto|SGD|MuSGD|Adam|AdamW|Adamax|NAdam|RAdam|RMSProp")
    patience: Optional[int] = Field(default=100, ge=0, le=100000)
    lr0: Optional[float] = Field(default=0.01, gt=0, le=10)
    lrf: Optional[float] = Field(default=0.01, ge=0, le=10)
    momentum: Optional[float] = Field(default=0.937, ge=0, le=1)
    weight_decay: Optional[float] = Field(default=0.0005, ge=0, le=1)
    warmup_epochs: Optional[float] = Field(default=3.0, ge=0, le=1000)
    cos_lr: Optional[bool] = Field(default=False)


class TaskConfigPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    epoch: int = Field(default=10, ge=1, le=10000)
    size: int = Field(default=640, ge=32, le=4096)
    batch: int = Field(default=8, ge=1, le=1024)
    device: str = Field(default="cpu")
    label_format: Optional[str] = Field(default=None, description="auto|bbox|obb")
    export_onnx: bool = False
    onnx_dynamic: bool = False
    onnx_simplify: bool = False
    dataset_cache_mode: Literal["off", "reuse", "refresh"] = "off"
    resume_model_id: Optional[int] = None
    augmentation: Optional[TrainingAugmentationConfig] = None
    optimizer_config: Optional[TrainingOptimizerConfig] = None


class TrainerStatusResponse(BaseModel):
    reachable: bool
    status: str
    version: Optional[str] = None
    mq_connected: bool = False
    max_concurrent: int = 0
    active_tasks: int = 0
    queued_tasks: int = 0
    available_devices: List[str] = Field(default_factory=lambda: ["cpu"])
    message: Optional[str] = None


class TaskSummaryResponse(BaseModel):
    total: int
    running: int
    completed: int


class TaskStreamEvent(BaseModel):
    event: str
    data: dict
