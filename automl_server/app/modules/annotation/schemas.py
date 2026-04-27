"""标注 Schema"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AnnotationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    annotation_type: int = Field(
        default=0, description="0=检测(BBox/OBB), 1=分类, 2=分割(Polygon), 3=MLLM, 4=姿态, 5=LLM")
    classes: Optional[str] = Field(default=None, description="分类项 JSON")
    storage_type: int = Field(default=1)
    prompt: Optional[str] = None
    assist_pipeline: Optional[str] = None
    dataset_id: Optional[int] = None


class AnnotationUpdate(BaseModel):
    name: Optional[str] = None
    classes: Optional[str] = None
    prompt: Optional[str] = None
    assist_pipeline: Optional[str] = None


class AnnotationResponse(BaseModel):
    id: int
    name: str
    annotation_type: int
    classes: Optional[str]
    storage_type: int
    save_path: Optional[str]
    prompt: Optional[str]
    assist_pipeline: Optional[str]
    dataset_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnotationFileResponse(BaseModel):
    id: int
    annotation_id: int
    file_name: str
    save_path: Optional[str]
    content: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AnnotationFileSave(BaseModel):
    file_name: str
    content: str


class AnnotationAssistRequest(BaseModel):
    file_name: str
    pipeline_id: Optional[str] = None
    shape: str = "bbox"
    target_classes: Optional[List[str]] = None
    replace_existing: bool = False
    params: dict = Field(default_factory=dict)


class AnnotationAssistPipelineResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    supported_annotation_types: List[int] = Field(default_factory=list)
    supported_shapes: List[str] = Field(default_factory=list)
    enabled: bool = True


class AnnotationAssistItem(BaseModel):
    label: str
    bbox: dict[str, int]
    confidence: Optional[float] = None
    source: Optional[str] = None


class AnnotationAssistResponse(BaseModel):
    file_name: str
    image_width: int
    image_height: int
    annotations: List[AnnotationAssistItem]
    replace_existing: bool
    debug: Optional[dict] = None
