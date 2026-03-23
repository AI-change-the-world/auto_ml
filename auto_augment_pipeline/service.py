from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capabilities import (
    Capability,
    DescribeImageCapability,
    DraftAnnotationCapability,
    ExtractWhiteAnnotationsCapability,
    RenderWhiteAnnotationOverlayCapability,
    UnderstandWhiteAnnotationsCapability,
)
from .config import RuntimeConfig
from .models import CapabilityDescriptor, ExecuteCapabilityRequest, PipelineDefinition, TaskPayload
from .pipeline import PipelineRunner
from .providers import BaseMultimodalProvider, ProviderRegistry


@dataclass
class ServiceExecutionContext:
    config: RuntimeConfig
    providers: ProviderRegistry

    def resolve_provider(
        self, explicit_name: str | None = None, role: str = "multimodal"
    ) -> BaseMultimodalProvider:
        provider_name = explicit_name or self._default_provider_name(role)
        if provider_name is None:
            names = self.providers.names()
            if len(names) == 1:
                provider_name = names[0]
            else:
                raise ValueError(f"no provider configured for role `{role}`")
        return self.providers.get(provider_name)

    def _default_provider_name(self, role: str) -> str | None:
        if role == "image_edit":
            return self.config.defaults.image_edit_provider or self.config.defaults.multimodal_provider
        if role == "ocr":
            return self.config.defaults.ocr_provider or self.config.defaults.multimodal_provider
        if role == "text":
            return self.config.defaults.text_provider or self.config.defaults.multimodal_provider
        return self.config.defaults.multimodal_provider


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
        context = ServiceExecutionContext(config=self.config, providers=self.providers)
        return capability.execute(
            payload=request.input,
            params=request.params,
            context=context,
            provider_name=request.provider,
        )

    def run_pipeline(
        self,
        *,
        name: str | None = None,
        definition: PipelineDefinition | None = None,
        payload: TaskPayload,
    ) -> Any:
        pipeline_definition = definition
        if pipeline_definition is None:
            if not name:
                raise ValueError("pipeline name or inline definition is required")
            pipeline_definition = self.config.pipelines.get(name)
            if pipeline_definition is None:
                raise ValueError(f"pipeline `{name}` is not configured")
        return self.pipeline_runner.run(pipeline_definition, payload)

    def _build_capabilities(self) -> dict[str, Capability]:
        items: list[Capability] = [
            DescribeImageCapability(),
            DraftAnnotationCapability(),
            RenderWhiteAnnotationOverlayCapability(),
            UnderstandWhiteAnnotationsCapability(),
            ExtractWhiteAnnotationsCapability(),
        ]
        return {item.name: item for item in items}
