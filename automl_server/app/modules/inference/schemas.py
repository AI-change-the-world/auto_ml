"""推理 Schema"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InferenceBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class InferencePoint(BaseModel):
    x: float
    y: float


class InferenceOBB(BaseModel):
    cx: float
    cy: float
    w: float
    h: float
    angle: float


class InferenceResultItem(BaseModel):
    type: str
    class_id: int
    class_name: str
    confidence: float
    box: Optional[InferenceBox] = None
    obb: Optional[InferenceOBB] = None
    points: Optional[List[InferencePoint]] = None


class InferencePredictResponse(BaseModel):
    success: bool
    model_id: Optional[int] = None
    model_name: Optional[str] = None
    task_kind: Optional[str] = None
    backend: Optional[str] = None
    device: Optional[str] = None
    results: List[InferenceResultItem] = Field(default_factory=list)
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    error: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class InferenceParams(BaseModel):
    input_type: Optional[str] = Field(default=None, description="输入类型: tile/mosaic/raw_aerial")
    inference_mode: Optional[str] = Field(default=None, description="推理模式: direct/tile/scene")
    tile_size: Optional[int] = Field(default=None, ge=64, description="切片尺寸")
    tile_overlap: Optional[float] = Field(default=None, ge=0, lt=1, description="切片重叠比例")
    merge_strategy: Optional[str] = Field(default=None, description="结果融合方式: nms/wbf")
    merge_iou: Optional[float] = Field(default=None, ge=0, le=1, description="融合 IoU 阈值")
    edge_filter: Optional[bool] = Field(default=None, description="是否过滤切片边缘结果")
    return_global_coords: Optional[bool] = Field(default=None, description="是否返回全局坐标")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="保留扩展参数")


class InferenceBase64Request(BaseModel):
    image: str
    inference_params: Optional[InferenceParams] = None


class InferenceHealthResponse(BaseModel):
    model_id: int
    model_name: Optional[str] = None
    task_kind: Optional[str] = None
    backend: Optional[str] = None
    is_deployed: bool
    backend_healthy: bool
    deployment_port: Optional[int] = None
    deployment_device: Optional[str] = None
    deployment_version: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None
