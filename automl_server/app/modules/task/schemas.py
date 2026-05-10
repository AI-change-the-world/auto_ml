"""任务 Schema"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict


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
    augmentation: Optional["TrainingAugmentationConfig"] = None


class TrainingAugmentationConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    enabled: bool = True
    mosaic: Optional[float] = Field(default=1.0, ge=0, le=1)
    mixup: Optional[float] = Field(default=0.0, ge=0, le=1)
    copy_paste: Optional[float] = Field(default=0.0, ge=0, le=1)
    close_mosaic: Optional[int] = Field(default=10, ge=0, le=10000)
    auto_augment: Optional[Literal["randaugment", "autoaugment", "augmix", "none"]] = Field(
        default="randaugment",
        description="classification only",
    )
    erasing: Optional[float] = Field(default=0.4, ge=0, le=1)


class TrainerStatusResponse(BaseModel):
    reachable: bool
    status: str
    version: Optional[str] = None
    mq_connected: bool = False
    max_concurrent: int = 0
    active_tasks: int = 0
    queued_tasks: int = 0
    message: Optional[str] = None


class TaskStreamEvent(BaseModel):
    event: str
    data: dict
