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


class InferenceBase64Request(BaseModel):
    image: str


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
