from __future__ import annotations

import os
import re
from typing import Callable

import yaml
from pydantic import BaseModel, Field

from .models import PipelineDefinition
from .nacos_config_center import get_config_center


class ProviderConfig(BaseModel):
    kind: str = "openai_compatible"
    role: str = "multimodal"
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    timeout_seconds: float = 60.0
    temperature: float = 0.0
    max_tokens: int = 1024
    extra_headers: dict[str, str] = Field(default_factory=dict)
    extra: dict[str, object] = Field(default_factory=dict)


class RuntimeConfig(BaseModel):
    service_name: str = "ai-pipeline-runtime"
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    pipelines: dict[str, PipelineDefinition] = Field(default_factory=dict)


def _expand_env_vars(raw: str) -> str:
    pattern = re.compile(r"\$\{([A-Z0-9_]+)\}")

    def replace(match: re.Match[str]) -> str:
        return os.getenv(match.group(1), "")

    return pattern.sub(replace, raw)


def parse_runtime_config(raw: str) -> RuntimeConfig:
    expanded = _expand_env_vars(raw)
    data = yaml.safe_load(expanded) or {}
    if not data:
        raise RuntimeError("Nacos config payload is empty")
    return RuntimeConfig.model_validate(data)


def get_runtime_config() -> RuntimeConfig:
    payload = get_config_center().get_config_data()
    if not payload:
        raise RuntimeError("AI_PIPELINE_RUNTIME config is empty")
    return RuntimeConfig.model_validate(payload)


def register_runtime_config_callback(name: str, callback: Callable[[RuntimeConfig], None]) -> None:
    def _wrapped(_old: dict, new: dict) -> None:
        callback(RuntimeConfig.model_validate(new))

    get_config_center().register_callback(name, _wrapped)


def unregister_runtime_config_callback(name: str) -> None:
    get_config_center().unregister_callback(name)
