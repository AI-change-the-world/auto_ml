"""部署 Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DeployRequest(BaseModel):
    model_id: int
    device: str = Field(default="cpu", description="部署设备: cpu/cuda")
    version: str = Field(default="v1")


class UndeployRequest(BaseModel):
    model_id: int


class RenameModelRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="模型名称")


class AvailableModelResponse(BaseModel):
    id: int
    name: Optional[str]
    model_path: Optional[str]
    onnx_model_path: Optional[str]
    model_type: Optional[str]
    dataset_id: Optional[int]
    task_id: Optional[int]
    loss: Optional[float]
    is_deployed: bool
    deployment_id: Optional[str]
    deployment_port: Optional[int]
    deployment_version: Optional[str]
    deployment_device: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeployStatusResponse(BaseModel):
    model_id: int
    is_deployed: bool
    deployment_id: Optional[str]
    port: Optional[int]
    version: Optional[str]
    device: Optional[str]
