from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capabilities import (
    AssistAnnotationCapability,
    Capability,
    DescribeImageCapability,
    DraftAnnotationCapability,
    ExtractWhiteAnnotationsCapability,
    RenderWhiteAnnotationOverlayCapability,
    UnderstandWhiteAnnotationsCapability,
)
from .config import ProfileConfig, RuntimeConfig
from .models import CapabilityDescriptor, ExecuteCapabilityRequest, PipelineDefinition, TaskPayload
from .pipeline import PipelineRunner
from .providers import BaseMultimodalProvider, ProviderRegistry


@dataclass
class ServiceExecutionContext:
    config: RuntimeConfig
    providers: ProviderRegistry
    profile_name: str | None = None
    provider_overrides: dict[str, str] | None = None

    def resolve_provider(
        self, explicit_name: str | None = None, role: str = "multimodal"
    ) -> BaseMultimodalProvider:
        provider_name = None
        if self.provider_overrides:
            provider_name = self.provider_overrides.get(role)
        provider_name = provider_name or explicit_name or self._profile_provider_name(role) or self._default_provider_name(role)
        if provider_name is None:
            names = self.providers.names()
            if len(names) == 1:
                provider_name = names[0]
            else:
                raise ValueError(f"no provider configured for role `{role}`")
        return self.providers.get(provider_name)

    def profile(self) -> ProfileConfig | None:
        if not self.profile_name:
            return None
        return self.config.profiles.get(self.profile_name)

    def _profile_provider_name(self, role: str) -> str | None:
        profile = self.profile()
        if profile is None:
            return None
        if role == "image_edit":
            return profile.image_edit_provider or profile.multimodal_provider
        if role == "ocr":
            return profile.ocr_provider or profile.multimodal_provider
        if role == "text":
            return profile.text_provider or profile.multimodal_provider
        return profile.multimodal_provider

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
        profile = self.config.profiles.get(request.profile) if request.profile else None
        if request.profile and profile is None:
            raise ValueError(f"profile `{request.profile}` is not configured")
        params = dict(profile.params) if profile is not None else {}
        params.update(request.params)
        context = ServiceExecutionContext(
            config=self.config,
            providers=self.providers,
            profile_name=request.profile,
            provider_overrides=request.provider_overrides,
        )
        return capability.execute(
            payload=request.input,
            params=params,
            context=context,
            provider_name=request.provider,
        )

    def run_pipeline(
        self,
        *,
        name: str | None = None,
        definition: PipelineDefinition | None = None,
        payload: TaskPayload,
        profile: str | None = None,
        params: dict[str, Any] | None = None,
        provider_overrides: dict[str, str] | None = None,
    ) -> Any:
        pipeline_definition = definition
        if pipeline_definition is None:
            if not name:
                raise ValueError("pipeline name or inline definition is required")
            pipeline_definition = self.config.pipelines.get(name)
            if pipeline_definition is None:
                raise ValueError(f"pipeline `{name}` is not configured")
        return self.pipeline_runner.run_with_options(
            pipeline_definition,
            payload,
            profile=profile,
            params=params,
            provider_overrides=provider_overrides,
        )

    def _build_capabilities(self) -> dict[str, Capability]:
        items: list[Capability] = [
            DescribeImageCapability(),
            DraftAnnotationCapability(),
            RenderWhiteAnnotationOverlayCapability(),
            UnderstandWhiteAnnotationsCapability(),
            ExtractWhiteAnnotationsCapability(),
            AssistAnnotationCapability(),
        ]
        return {item.name: item for item in items}
