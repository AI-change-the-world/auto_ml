"""标注 Schema"""
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class AnnotationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    annotation_type: int = Field(
        default=0, description="0=检测(BBox/OBB), 1=分类, 2=分割(Polygon), 3=MLLM, 4=姿态, 5=LLM")
    classes: Optional[str] = Field(default=None, description="分类项 JSON")
    storage_type: int = Field(default=1)
    prompt: Optional[str] = None
    assist_pipeline: Optional[str] = None
    default_ai_pipeline_binding_id: Optional[int] = None
    dataset_id: Optional[int] = None


class AnnotationUpdate(BaseModel):
    name: Optional[str] = None
    classes: Optional[str] = None
    prompt: Optional[str] = None
    assist_pipeline: Optional[str] = None
    default_ai_pipeline_binding_id: Optional[int] = None


class AnnotationResponse(BaseModel):
    id: int
    name: str
    annotation_type: int
    classes: Optional[str]
    storage_type: int
    save_path: Optional[str]
    prompt: Optional[str]
    assist_pipeline: Optional[str]
    default_ai_pipeline_binding_id: Optional[int]
    dataset_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnotationTypeDefinitionResponse(BaseModel):
    value: int
    code: str
    label: str
    color: str
    icon_key: str
    supports_classes: bool


class AnnotationRecordSave(BaseModel):
    sample_item_id: int
    content: dict[str, Any] = Field(default_factory=dict)
    status: str = "saved"


class AnnotationRecordResponse(BaseModel):
    id: int
    annotation_id: int
    sample_item_id: int
    annotation_type: int
    status: str
    content: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class AnnotationRecordBatchQuery(BaseModel):
    sample_item_ids: List[int] = Field(default_factory=list)


class AnnotationAssistRequest(BaseModel):
    sample_item_id: int
    pipeline_id: Optional[str] = None
    binding_id: Optional[int] = None
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
    sample_item_id: int
    item_key: str
    image_width: int
    image_height: int
    annotations: List[AnnotationAssistItem]
    replace_existing: bool
    debug: Optional[dict] = None


class AnnotationExportItem(BaseModel):
    prompt: dict[str, Any]
    chosen: str
    rejected: str
    chosen_response_id: str
    rejected_response_id: str
    sample_item_id: int
    annotation_id: int
    reason: Optional[str] = None
