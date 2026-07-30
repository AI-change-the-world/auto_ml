"""工作台智能助手 API schemas。"""
from typing import Optional

from pydantic import BaseModel, Field


class AssistantConfigResponse(BaseModel):
    enabled: bool = False
    provider_display_name: Optional[str] = None
    provider_kind: Optional[str] = None
    base_url: Optional[str] = None
    api_key_configured: bool = False
    model: Optional[str] = None
    timeout_seconds: Optional[float] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None


class AssistantConfigUpdate(BaseModel):
    enabled: bool = False
    base_url: Optional[str] = Field(default=None, max_length=512)
    api_key: Optional[str] = None
    model: Optional[str] = Field(default=None, max_length=255)
    timeout_seconds: float = Field(default=60, ge=1, le=600)
    temperature: float = Field(default=0.2, ge=0.0, le=5.0)
    max_tokens: int = Field(default=2048, ge=1, le=65536)
    system_prompt: Optional[str] = None


class AssistantChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=12000)
    page_context: Optional[str] = Field(default=None, max_length=512)
    language: Optional[str] = Field(default=None, max_length=16)


class AssistantAction(BaseModel):
    key: str
    label: str
    path: str


class AssistantChatResponse(BaseModel):
    content: str
    actions: list[AssistantAction] = Field(default_factory=list)
