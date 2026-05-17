from __future__ import annotations

from typing import Any

from ..models import AnnotationResult, TaskPayload
from .base import Capability, ProviderResolver
from .overlay import (
    ExtractWhiteAnnotationsCapability,
    RenderWhiteAnnotationOverlayCapability,
    UnderstandWhiteAnnotationsCapability,
)


class AssistAnnotationCapability(Capability):
    name = "assist_annotation"
    description = "Render white annotation overlays, extract them, and fallback to multimodal understanding when needed."
    requires_provider = True

    def __init__(self) -> None:
        self._render = RenderWhiteAnnotationOverlayCapability()
        self._extract = ExtractWhiteAnnotationsCapability()
        self._understand = UnderstandWhiteAnnotationsCapability()

    def execute(
        self,
        payload: TaskPayload,
        params: dict[str, Any],
        context: ProviderResolver,
        provider_name: str | None = None,
    ) -> AnnotationResult:
        if payload.image is None:
            raise ValueError("assist_annotation requires `image`")

        render_result = self._render.execute(
            payload=payload,
            params=params,
            context=context,
            provider_name=provider_name,
        )
        overlay_payload = TaskPayload(
            image=payload.image,
            overlay_image=render_result.overlay_image,
            classes=list(payload.classes),
            prompt=payload.prompt,
            text=payload.text,
            metadata=dict(payload.metadata),
        )
        extract_result = self._extract.execute(
            payload=overlay_payload,
            params=params,
            context=context,
            provider_name=provider_name,
        )

        fallback_reason = self._fallback_reason(extract_result, params)
        final_result = extract_result
        understand_result = None
        understand_error = None

        if fallback_reason is not None:
            try:
                understand_result = self._understand.execute(
                    payload=overlay_payload,
                    params=params,
                    context=context,
                    provider_name=provider_name,
                )
            except Exception as exc:
                understand_error = str(exc)

            if understand_result is not None and self._prefer_understand_result(
                understand_result,
                extract_result,
            ):
                final_result = understand_result

        provider_chain = [render_result.provider]
        if final_result.provider and final_result.provider not in provider_chain:
            provider_chain.append(final_result.provider)

        return AnnotationResult(
            capability=self.name,
            provider=" -> ".join(item for item in provider_chain if item),
            image_width=final_result.image_width,
            image_height=final_result.image_height,
            annotations=final_result.annotations,
            summary=final_result.summary or "Annotation assistance completed.",
            raw={
                "render_provider": render_result.provider,
                "extract_provider": extract_result.provider,
                "understand_provider": understand_result.provider if understand_result is not None else None,
                "fallback_reason": fallback_reason,
                "fallback_used": final_result is understand_result,
                "extract_annotation_count": len(extract_result.annotations),
                "extract_labeled_count": self._labeled_count(extract_result),
                "understand_annotation_count": len(understand_result.annotations) if understand_result is not None else 0,
                "understand_labeled_count": self._labeled_count(understand_result) if understand_result is not None else 0,
                "understand_error": understand_error,
            },
        )

    def _fallback_reason(
        self,
        result: AnnotationResult,
        params: dict[str, Any],
    ) -> str | None:
        min_annotation_count = int(params.get("assist_min_annotation_count", 1))
        min_labeled_ratio = float(params.get("assist_min_labeled_ratio", 0.75))
        if len(result.annotations) < min_annotation_count:
            return "extract_annotation_count_below_threshold"
        labeled_count = self._labeled_count(result)
        if labeled_count == 0:
            return "extract_has_no_labels"
        if labeled_count / max(1, len(result.annotations)) < min_labeled_ratio:
            return "extract_labeled_ratio_below_threshold"
        return None

    def _prefer_understand_result(
        self,
        understand_result: AnnotationResult,
        extract_result: AnnotationResult,
    ) -> bool:
        understand_labeled = self._labeled_count(understand_result)
        extract_labeled = self._labeled_count(extract_result)
        if understand_labeled > extract_labeled:
            return True
        if understand_labeled == extract_labeled and len(understand_result.annotations) > len(extract_result.annotations):
            return True
        return False

    def _labeled_count(self, result: AnnotationResult | None) -> int:
        if result is None:
            return 0
        return sum(1 for item in result.annotations if item.label.strip())
