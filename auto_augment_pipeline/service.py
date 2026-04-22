from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

_CAPABILITIES_DIR = os.path.join(os.path.dirname(__file__), "capabilities")
if _CAPABILITIES_DIR not in sys.path:
    sys.path.insert(0, _CAPABILITIES_DIR)

from capabilities import (
    AssistAnnotationCapability,
    Capability,
    DescribeImageCapability,
    DraftAnnotationCapability,
    DraftAnnotationPreviewCapability,
    ExtractWhiteAnnotationsCapability,
    RenderWhiteAnnotationOverlayCapability,
    UnderstandWhiteAnnotationsCapability,
)
from config import RuntimeConfig
from models import CapabilityDescriptor, ExecuteCapabilityRequest, PipelineDefinition, TaskPayload
from pipeline import PipelineRunner
from providers import BaseMultimodalProvider, ProviderRegistry


@dataclass
class ServiceExecutionContext:
    config: RuntimeConfig
    providers: ProviderRegistry

    def resolve_provider(
        self, explicit_name: str | None = None, role: str = "multimodal"
    ) -> BaseMultimodalProvider:
        provider_name = explicit_name
        if provider_name is None:
            names = self.providers.names()
            if len(names) == 1:
                provider_name = names[0]
            else:
                raise ValueError(
                    f"provider must be specified explicitly for role `{role}` when multiple providers are configured"
                )
        return self.providers.get(provider_name)


class AutoAugmentService:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.providers = ProviderRegistry.from_config(config)
        self.capabilities = self._build_capabilities()
        self.pipeline_runner = PipelineRunner(self.execute_capability)

    def reload(self, config: RuntimeConfig) -> None:
        self.config = config
        self.providers = ProviderRegistry.from_config(config)
        self.capabilities = self._build_capabilities()
        self.pipeline_runner = PipelineRunner(self.execute_capability)

    def list_capabilities(self) -> list[CapabilityDescriptor]:
        return [capability.describe() for capability in self.capabilities.values()]

    def list_pipelines(self) -> list[PipelineDefinition]:
        return list(self.config.pipelines.values())

    def execute_capability(
        self, capability_name: str, request: ExecuteCapabilityRequest
    ) -> Any:
        capability = self.capabilities.get(capability_name)
        if capability is None:
            raise ValueError(f"unsupported capability `{capability_name}`")
        context = ServiceExecutionContext(
            config=self.config,
            providers=self.providers,
        )
        return capability.execute(
            payload=request.input,
            params=dict(request.params),
            context=context,
            provider_name=request.provider,
        )

    def run_pipeline(
        self,
        *,
        name: str | None = None,
        definition: PipelineDefinition | None = None,
        payload: TaskPayload,
        params: dict[str, Any] | None = None,
    ) -> Any:
        pipeline_definition = definition
        if pipeline_definition is None:
            if not name:
                raise ValueError(
                    "pipeline name or inline definition is required")
            pipeline_definition = self.config.pipelines.get(name)
            if pipeline_definition is None:
                raise ValueError(f"pipeline `{name}` is not configured")
        return self.pipeline_runner.run_with_options(
            pipeline_definition,
            payload,
            params=params,
        )

    def _build_capabilities(self) -> dict[str, Capability]:
        items: list[Capability] = [
            DescribeImageCapability(),
            DraftAnnotationCapability(),
            DraftAnnotationPreviewCapability(),
            RenderWhiteAnnotationOverlayCapability(),
            UnderstandWhiteAnnotationsCapability(),
            ExtractWhiteAnnotationsCapability(),
            AssistAnnotationCapability(),
        ]
        return {item.name: item for item in items}
