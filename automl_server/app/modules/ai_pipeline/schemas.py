"""AI Pipeline schemas"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AiPipelineTemplateListItem(BaseModel):
    id: int
    template_key: str
    name: str
    description: Optional[str] = None
    scene_type: str
    input_kind: Optional[str] = None
    output_kind: Optional[str] = None
    status: str
    latest_version: int
    published_version: Optional[int] = None
    is_builtin: bool = False
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AiPipelineTemplateCreate(BaseModel):
    template_key: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scene_type: str = Field(..., min_length=1, max_length=64)
    input_kind: Optional[str] = Field(default=None, max_length=64)
    output_kind: Optional[str] = Field(default=None, max_length=64)
    status: str = Field(default="draft", max_length=32)
    is_builtin: bool = False
    created_by: Optional[str] = Field(default=None, max_length=64)


class AiPipelineTemplateVersionCreate(BaseModel):
    version: int = Field(..., ge=1)
    definition_json: dict[str, Any] | list[Any] | str
    form_schema_json: Optional[dict[str, Any] | list[Any] | str] = None
    change_note: Optional[str] = Field(default=None, max_length=512)
    is_published: bool = False
    created_by: Optional[str] = Field(default=None, max_length=64)


class AiPipelineTemplateDraftSave(BaseModel):
    definition_json: dict[str, Any] | list[Any] | str
    form_schema_json: Optional[dict[str, Any] | list[Any] | str] = None
    change_note: Optional[str] = Field(default=None, max_length=512)
    created_by: Optional[str] = Field(default=None, max_length=64)


class AiPipelineTemplateDetail(AiPipelineTemplateListItem):
    definition_json: Optional[dict[str, Any] | list[Any] | str] = None
    form_schema_json: Optional[dict[str, Any] | list[Any] | str] = None
    change_note: Optional[str] = None


class AiPipelineBindingCreate(BaseModel):
    binding_type: str = Field(..., min_length=1, max_length=64)
    binding_target_id: int = Field(..., gt=0)
    template_id: int = Field(..., gt=0)
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    is_default: bool = False
    runtime_input_defaults_json: Optional[dict[str, Any] | list[Any] | str] = None
    resource_bindings_json: Optional[dict[str, Any] | list[Any] | str] = None
    created_by: Optional[str] = Field(default=None, max_length=64)


class AiPipelineBindingUpdate(BaseModel):
    template_id: Optional[int] = Field(default=None, gt=0)
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    runtime_input_defaults_json: Optional[dict[str, Any] | list[Any] | str] = None
    resource_bindings_json: Optional[dict[str, Any] | list[Any] | str] = None


class AiPipelineBindingResponse(BaseModel):
    id: int
    binding_type: str
    binding_target_id: int
    template_id: int
    template_version: int
    template_key: Optional[str] = None
    template_name: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    pipeline_type: Optional[str] = None
    supported_annotation_types: list[int] = Field(default_factory=list)
    supported_shapes: list[str] = Field(default_factory=list)
    enabled: bool = True
    is_default: bool = False
    runtime_input_defaults_json: Optional[dict[str, Any] | list[Any] | str] = None
    resource_bindings_json: Optional[dict[str, Any] | list[Any] | str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AiPipelineModelResourceItem(BaseModel):
    resource_id: str
    model_id: int
    display_name: str
    model_name: Optional[str] = None
    model_type: Optional[str] = None
    runtime_template: Optional[str] = None
    is_deployed: bool = False
    deployment_device: Optional[str] = None
    deployed_at: Optional[datetime] = None


class AiPipelineProviderResourceItem(BaseModel):
    id: Optional[int] = None
    resource_id: str
    provider_name: str
    display_name: str
    description: Optional[str] = None
    role: str
    kind: Optional[str] = None
    base_url: Optional[str] = None
    api_key_configured: bool = False
    model: Optional[str] = None
    timeout_seconds: Optional[float] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    extra_headers_json: Optional[dict[str, Any] | list[Any] | str] = None
    extra_json: Optional[dict[str, Any] | list[Any] | str] = None
    enabled: bool = True
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AiPipelineProviderResourceOption(BaseModel):
    id: Optional[int] = None
    resource_id: str
    provider_name: str
    display_name: str
    role: str
    kind: Optional[str] = None
    model: Optional[str] = None
    enabled: bool = True


class AiPipelineProviderResourceCreate(BaseModel):
    resource_id: str = Field(..., min_length=1, max_length=128)
    provider_name: str = Field(..., min_length=1, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    kind: str = Field(..., min_length=1, max_length=64)
    role: str = Field(..., min_length=1, max_length=64)
    base_url: Optional[str] = Field(default=None, max_length=512)
    api_key: Optional[str] = None
    model: Optional[str] = Field(default=None, max_length=255)
    timeout_seconds: float = Field(default=60, ge=1, le=600)
    temperature: float = Field(default=0.0, ge=0.0, le=5.0)
    max_tokens: int = Field(default=1024, ge=1, le=65536)
    extra_headers_json: Optional[dict[str, Any] | list[Any] | str] = None
    extra_json: Optional[dict[str, Any] | list[Any] | str] = None
    enabled: bool = True
    created_by: Optional[str] = Field(default=None, max_length=64)


class AiPipelineProviderResourceUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    kind: Optional[str] = Field(default=None, min_length=1, max_length=64)
    role: Optional[str] = Field(default=None, min_length=1, max_length=64)
    base_url: Optional[str] = Field(default=None, max_length=512)
    api_key: Optional[str] = None
    model: Optional[str] = Field(default=None, max_length=255)
    timeout_seconds: Optional[float] = Field(default=None, ge=1, le=600)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=65536)
    extra_headers_json: Optional[dict[str, Any] | list[Any] | str] = None
    extra_json: Optional[dict[str, Any] | list[Any] | str] = None
    enabled: Optional[bool] = None


class AiPipelineCapabilityFieldOption(BaseModel):
    label: str
    value: str | int | float | bool


class AiPipelineCapabilityField(BaseModel):
    key: str
    label: str
    value_type: str = "string"
    required: bool = False
    description: Optional[str] = None
    widget: Optional[str] = None
    default_value: Any = None
    placeholder: Optional[str] = None
    binding_kind: str = "parameter"
    resource_type: Optional[str] = None
    task_kind: Optional[str] = None
    deployed_only: Optional[bool] = None
    options: list[AiPipelineCapabilityFieldOption] = Field(default_factory=list)


class AiPipelineCapabilityContextTarget(BaseModel):
    key: str
    label: str
    description: Optional[str] = None
    accepted_output_types: list[str] = Field(default_factory=list)


class AiPipelineCapabilityItem(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    category: str = "general"
    requires_provider: bool = False
    provider_role: Optional[str] = None
    recommended_output_key: Optional[str] = None
    input_types: list[str] = Field(default_factory=list)
    output_type: Optional[str] = None
    scene_types: list[str] = Field(default_factory=list)
    parameter_fields: list[AiPipelineCapabilityField] = Field(default_factory=list)
    context_mapping_targets: list[AiPipelineCapabilityContextTarget] = Field(default_factory=list)
