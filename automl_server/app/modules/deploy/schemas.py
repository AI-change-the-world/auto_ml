"""部署 Schema"""
import json
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class DeployRequest(BaseModel):
    model_id: int
    device: str = Field(default="cpu", description="部署设备: cpu/cuda")
    version: str = Field(default="v1")


class UndeployRequest(BaseModel):
    model_id: int


class RenameModelRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="模型名称")


class OnnxIoTensorSignature(BaseModel):
    name: str
    shape: list[str]
    dtype: Optional[str] = None


class UploadOnnxModelResponse(BaseModel):
    id: int
    name: Optional[str]
    onnx_model_path: str
    model_type: str
    runtime_template: str
    class_names: list[str] = Field(default_factory=list)
    input_signature: list[OnnxIoTensorSignature] = Field(default_factory=list)
    output_signature: list[OnnxIoTensorSignature] = Field(default_factory=list)
    created_at: datetime


class AvailableModelResponse(BaseModel):
    id: int
    name: Optional[str]
    model_path: Optional[str]
    onnx_model_path: Optional[str]
    model_type: Optional[str]
    runtime_template: Optional[str]
    dataset_id: Optional[int]
    task_id: Optional[int]
    loss: Optional[float]
    onnx_input_signature: Optional[str]
    onnx_output_signature: Optional[str]
    is_deployed: bool
    deployment_id: Optional[str]
    deployment_port: Optional[int]
    deployment_version: Optional[str]
    deployment_device: Optional[str]
    deployed_at: Optional[datetime]
    inference_count: int = 0
    last_inference_at: Optional[datetime]
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


class DeploymentRuntimeStatus(BaseModel):
    status: str = "unknown"
    backend: Optional[str] = None
    task_kind: Optional[str] = None
    healthy: bool = False
    detail: Optional[dict] = None


class DeploymentOverviewItem(BaseModel):
    model_id: int
    model_name: Optional[str]
    model_type: Optional[str]
    runtime_template: Optional[str]
    task_id: Optional[int]
    dataset_id: Optional[int]
    deployment_id: Optional[str]
    deployment_port: Optional[int]
    deployment_version: Optional[str]
    deployment_device: Optional[str]
    is_deployed: bool
    deployed_at: Optional[datetime]
    inference_count: int = 0
    last_inference_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    runtime_status: DeploymentRuntimeStatus


class DeploymentOverviewSummary(BaseModel):
    total_models: int
    active_deployments: int
    healthy_deployments: int
    total_inference_calls: int


class DeploymentOverviewResponse(BaseModel):
    summary: DeploymentOverviewSummary
    items: list[DeploymentOverviewItem]


class ModelInferenceLogResponse(BaseModel):
    id: int
    model_id: int
    request_type: Optional[str]
    success: bool
    duration_ms: Optional[int]
    result_count: int
    image_width: Optional[int]
    image_height: Optional[int]
    error_message: Optional[str]
    client_ip: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ModelInferenceMetricsResponse(BaseModel):
    model_id: int
    inference_count: int = 0
    last_inference_at: Optional[datetime]
    success_count: int = 0
    failure_count: int = 0
    avg_duration_ms: Optional[float]
    last_24h_count: int = 0


class ModelInferenceActivityResponse(BaseModel):
    metrics: ModelInferenceMetricsResponse
    logs: list[ModelInferenceLogResponse]


class DeploymentDetailResponse(BaseModel):
    item: DeploymentOverviewItem
    metrics: ModelInferenceMetricsResponse


class UploadOnnxModelRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="模型名称")
    template: Literal["ultralytics_detection", "ultralytics_classification"] = Field(
        ...,
        description="推理模板",
    )
    class_names: str = Field(default="[]", description="类别名称 JSON 数组或分隔字符串")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("name cannot be empty")
        return normalized

    @field_validator("class_names")
    @classmethod
    def normalize_class_names(cls, value: str) -> str:
        text = (value or "").strip()
        if not text:
            return "[]"
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return json.dumps(parsed, ensure_ascii=False)
        except Exception:
            pass
        return text
