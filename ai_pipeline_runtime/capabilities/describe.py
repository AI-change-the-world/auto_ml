from __future__ import annotations

from typing import Any

from models import DescriptionResult, TaskPayload
from .base import Capability, ProviderResolver, capability_metadata


@capability_metadata(
    display_name="图像描述",
    category="multimodal",
    provider_role="multimodal",
    recommended_output_key="scene_description",
    input_types=["image"],
    output_type="text",
    scene_types=["assist_annotation", "general"],
    parameter_fields=[
        {
            "key": "prompt",
            "label": "提示词",
            "widget": "textarea",
            "description": "为空时使用默认图像描述提示词。",
            "default_value": "请用中文简要描述图像中的主要对象、动作、场景和与标注有关的关键信息，保持简洁。",
        },
        {
            "key": "temperature",
            "label": "Temperature",
            "value_type": "number",
            "widget": "number",
            "default_value": 0.1,
        },
        {
            "key": "max_tokens",
            "label": "最大输出 Token",
            "value_type": "number",
            "widget": "number",
            "default_value": 512,
        },
    ],
)
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
            or "请用中文简要描述图像中的主要对象、动作、场景和与标注有关的关键信息，保持简洁。"
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
