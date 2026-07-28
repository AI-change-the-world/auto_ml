"""Schemas for dataset batch annotation runs."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AiPipelineBatchScriptResponse(BaseModel):
    key: str
    version: str
    name: str
    description: str | None = None
    supported_data_types: list[int] = Field(default_factory=list)
    supported_annotation_types: list[int] = Field(default_factory=list)
    parameter_fields: list[dict[str, Any]] = Field(default_factory=list)


class AiPipelineBatchRunCreate(BaseModel):
    dataset_id: int = Field(..., gt=0)
    annotation_id: int = Field(..., gt=0)
    script_key: str = Field(..., min_length=1, max_length=128)
    selection_mode: str = Field(default="all", pattern="^(all|unannotated|selected)$")
    sample_item_ids: list[int] = Field(default_factory=list, max_length=10000)
    overwrite_policy: str = Field(
        default="skip_existing",
        pattern="^(skip_existing|overwrite_draft|overwrite_all)$",
    )
    script_params: dict[str, Any] = Field(default_factory=dict)
    batch_size: int = Field(default=20, ge=1, le=100)
    parallelism: int = Field(default=1, ge=1, le=4)


class AiPipelineBatchRunResponse(BaseModel):
    id: int
    run_id: str
    dataset_id: int
    annotation_id: int
    script_key: str
    script_version: str
    status: str
    selection_mode: str
    overwrite_policy: str
    batch_size: int
    parallelism: int
    total_count: int
    succeeded_count: int
    failed_count: int
    skipped_count: int
    canceled_count: int
    progress: int
    cancel_requested: bool
    script_params: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AiPipelineBatchRunItemResponse(BaseModel):
    id: int
    sample_item_id: int
    item_key: str
    status: str
    attempt_count: int
    annotation_record_id: int | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AiPipelineBatchRunEventResponse(BaseModel):
    id: int
    event_type: str
    event_payload: dict[str, Any] | list[Any] | str | None = None
    created_at: datetime | None = None
