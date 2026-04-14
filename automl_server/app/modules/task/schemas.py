"""任务 Schema"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    task_type: int = Field(default=0, description="0=检测, 1=分类")
    dataset_id: int
    annotation_id: Optional[int] = None
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


class TrainerStatusResponse(BaseModel):
    reachable: bool
    status: str
    version: Optional[str] = None
    mq_connected: bool = False
    max_concurrent: int = 0
    active_tasks: int = 0
    queued_tasks: int = 0
    message: Optional[str] = None
