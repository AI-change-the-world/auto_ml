from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from capabilities import (
    AssistAnnotationCapability,
    Capability,
    DescribeImageCapability,
    DraftAnnotationCapability,
    DraftAnnotationPreviewCapability,
    ExtractWhiteAnnotationsCapability,
    OnnxDetectCapability,
    RenderWhiteAnnotationOverlayCapability,
    UnderstandWhiteAnnotationsCapability,
)
from config import ProviderConfig, RuntimeConfig
from models import CapabilityDescriptor, ExecuteCapabilityRequest, PipelineDefinition, TaskPayload
from pipeline import PipelineRunner
from providers import BaseMultimodalProvider, ProviderRegistry


@dataclass
class ServiceExecutionContext:
    config: RuntimeConfig
    providers: ProviderRegistry
    provider_overrides: dict[str, BaseMultimodalProvider] = field(default_factory=dict)

    def resolve_provider_name_from_params(
        self,
        params: dict[str, Any] | None,
        *,
        role: str = "multimodal",
    ) -> str | None:
        if not isinstance(params, dict):
            return None
        resource_bindings = params.get("resource_bindings")
        if not isinstance(resource_bindings, dict):
            return None

        preferred_slots: list[str] = []
        explicit_slot = str(params.get("provider_resource_slot") or "").strip()
        if explicit_slot:
            preferred_slots.append(explicit_slot)
        preferred_slots.extend([
            f"{role}_provider",
            "provider",
        ])

        for slot_key in preferred_slots:
            slot_value = resource_bindings.get(slot_key)
            provider_name = self._read_provider_name(slot_value)
            if provider_name:
                return provider_name

        for slot_value in resource_bindings.values():
            provider_name = self._read_provider_name(slot_value)
            if provider_name:
                return provider_name
        return None

    def _read_provider_name(self, value: Any) -> str | None:
        if isinstance(value, dict):
            candidate = value.get("provider_name")
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
            resource_id = value.get("resource_id")
            if isinstance(resource_id, str) and resource_id.startswith("provider:"):
                text = resource_id.split(":", 1)[1].strip()
                return text or None
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("provider:"):
                text = text.split(":", 1)[1].strip()
            return text or None
        return None

    def resolve_provider(
        self, explicit_name: str | None = None, role: str = "multimodal"
    ) -> BaseMultimodalProvider:
        provider_name = explicit_name
        if provider_name and provider_name in self.provider_overrides:
            return self.provider_overrides[provider_name]
        if provider_name is not None:
            return self.providers.get(provider_name)

        override_candidates = [
            provider
            for provider in self.provider_overrides.values()
            if provider.role == role
        ]
        if len(override_candidates) == 1:
            return override_candidates[0]
        if len(override_candidates) > 1:
            raise ValueError(
                f"provider must be specified explicitly for role `{role}` when multiple inline providers are configured"
            )

        names = self.providers.names()
        if len(names) == 1:
            provider_name = names[0]
        else:
            raise ValueError(
                f"provider must be specified explicitly for role `{role}` when multiple providers are configured"
            )
        return self.providers.get(provider_name)

    def load_provider_overrides(self, params: dict[str, Any] | None) -> None:
        if not isinstance(params, dict):
            return
        resource_bindings = params.get("resource_bindings")
        if not isinstance(resource_bindings, dict):
            return
        for binding in resource_bindings.values():
            if not isinstance(binding, dict):
                continue
            provider_name = self._read_provider_name(binding)
            provider_config = binding.get("provider_config")
            if not provider_name or not isinstance(provider_config, dict):
                continue
            self.provider_overrides[provider_name] = ProviderRegistry.build_provider(
                provider_name,
                ProviderConfig.model_validate(provider_config),
            )


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
        context.load_provider_overrides(request.params)
        provider_name = request.provider or context.resolve_provider_name_from_params(
            request.params,
            role=request.provider_role or "multimodal",
        )
        return capability.execute(
            payload=request.input,
            params=dict(request.params),
            context=context,
            provider_name=provider_name,
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
            OnnxDetectCapability(),
            DraftAnnotationPreviewCapability(),
            RenderWhiteAnnotationOverlayCapability(),
            UnderstandWhiteAnnotationsCapability(),
            ExtractWhiteAnnotationsCapability(),
            AssistAnnotationCapability(),
        ]
        return {item.name: item for item in items}
