"""标注 Schema"""
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.modules.dataset.schemas import SampleItemResponse


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


class AnnotationSummaryResponse(BaseModel):
    total: int
    recent_annotations: list[AnnotationResponse] = Field(default_factory=list)


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
    collaborator_token: Optional[str] = None
    collab_state: Optional[str] = None


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


class AnnotationCollaboratorResponse(BaseModel):
    id: int
    annotation_id: int
    display_name: str
    token: str
    status: str
    last_active_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AnnotationCollaborationSessionRequest(BaseModel):
    token: Optional[str] = None


class AnnotationCollaborationSessionResponse(BaseModel):
    collaborator: AnnotationCollaboratorResponse


class AnnotationCollaborationClaimRequest(BaseModel):
    collaborator_token: str
    batch_size: int = Field(default=20, ge=1, le=100)


class AnnotationCollaborationClaimResponse(BaseModel):
    assigned_count: int


class AnnotationSampleAssignmentResponse(BaseModel):
    id: int
    annotation_id: int
    sample_item_id: int
    collaborator_id: int
    status: str
    lease_expires_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    collab_state: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AnnotationCollaborationSamplesResponse(BaseModel):
    collaborator: AnnotationCollaboratorResponse
    samples: list[SampleItemResponse] = Field(default_factory=list)
    records: list[AnnotationRecordResponse] = Field(default_factory=list)
    assignments: list[AnnotationSampleAssignmentResponse] = Field(default_factory=list)
    page: int
    page_size: int
    total: int


class AnnotationCollaborationStatsResponse(BaseModel):
    total: int
    completed: int
    assigned_to_me: int
    pending_mine: int
    available: int


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


class AnnotationAssistPipelineDetailResponse(AnnotationAssistPipelineResponse):
    steps: list[dict[str, Any]] = Field(default_factory=list)


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
