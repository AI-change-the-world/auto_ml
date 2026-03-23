from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class ImagePayload(BaseModel):
    path: str | None = None
    base64_data: str | None = None
    mime_type: str = "image/png"

    @model_validator(mode="after")
    def validate_source(self) -> "ImagePayload":
        if not self.path and not self.base64_data:
            raise ValueError("either `path` or `base64_data` must be provided")
        return self


class TaskPayload(BaseModel):
    image: ImagePayload | None = None
    overlay_image: ImagePayload | None = None
    classes: list[str] = Field(default_factory=list)
    prompt: str | None = None
    text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def primary_image(self) -> ImagePayload | None:
        return self.overlay_image or self.image


class AnnotationItem(BaseModel):
    label: str
    bbox: dict[str, int]
    label_anchor: dict[str, int] | None = None
    confidence: float | None = None
    source: str | None = None


class AnnotationResult(BaseModel):
    capability: str
    provider: str | None = None
    image_width: int
    image_height: int
    annotations: list[AnnotationItem] = Field(default_factory=list)
    summary: str | None = None
    raw: dict[str, Any] | list[Any] | None = None


class DescriptionResult(BaseModel):
    capability: str
    provider: str
    summary: str
    raw_text: str


class OverlayRenderResult(BaseModel):
    capability: str
    provider: str
    overlay_image: ImagePayload
    edit_prompt: str
    classes: list[str] = Field(default_factory=list)
    summary: str | None = None
    raw: dict[str, Any] | list[Any] | None = None


class CapabilityDescriptor(BaseModel):
    name: str
    description: str
    requires_provider: bool = False


class ExecuteCapabilityRequest(BaseModel):
    provider: str | None = None
    input: TaskPayload
    params: dict[str, Any] = Field(default_factory=dict)


class PipelineStep(BaseModel):
    name: str
    capability: str
    input_key: str = "input"
    output_key: str | None = None
    provider: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    context_mapping: dict[str, str] = Field(default_factory=dict)


class PipelineDefinition(BaseModel):
    name: str
    description: str | None = None
    steps: list[PipelineStep] = Field(default_factory=list)


class StepExecutionResult(BaseModel):
    name: str
    capability: str
    output_key: str


class PipelineRunResult(BaseModel):
    pipeline: str
    description: str | None = None
    steps: list[StepExecutionResult] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class InlinePipelineRunRequest(BaseModel):
    definition: PipelineDefinition
    input: TaskPayload
