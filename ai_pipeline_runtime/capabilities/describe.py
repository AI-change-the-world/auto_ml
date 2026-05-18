from __future__ import annotations

from typing import Any

from models import DescriptionResult, TaskPayload
from .base import Capability, ProviderResolver


class DescribeImageCapability(Capability):
    name = "describe_image"
    description = "Use a multimodal model to describe the scene, objects, and context."
    requires_provider = True

    def execute(
        self,
        payload: TaskPayload,
        params: dict[str, Any],
        context: ProviderResolver,
        provider_name: str | None = None,
    ) -> DescriptionResult:
        image = payload.primary_image
        if image is None:
            raise ValueError("describe_image requires `image` or `overlay_image`")

        provider = context.resolve_provider(provider_name, role="multimodal")
        prompt = (
            payload.prompt
            or params.get("prompt")
            or "Describe the image in Chinese. Focus on objects, actions, and annotation-relevant details."
        )
        summary = provider.generate_text(
            prompt=prompt,
            image=image,
            system_prompt="You are a careful visual analyst for data annotation.",
            temperature=float(params.get("temperature", 0.1)),
            max_tokens=int(params.get("max_tokens", 512)),
        )
        return DescriptionResult(
            capability=self.name,
            provider=provider.name,
            summary=summary,
            raw_text=summary,
        )
