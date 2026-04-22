from __future__ import annotations

import logging
from typing import Any

from models import AnnotationResult, TaskPayload
from utils import image_size
from base import AnnotationNormalizationMixin, Capability, ProviderResolver

logger = logging.getLogger(__name__)


class DraftAnnotationCapability(AnnotationNormalizationMixin, Capability):
    name = "draft_annotation"
    description = "Ask a multimodal model to draft bounding boxes with strict class constraints."
    requires_provider = True

    def execute(
        self,
        payload: TaskPayload,
        params: dict[str, Any],
        context: ProviderResolver,
        provider_name: str | None = None,
    ) -> AnnotationResult:
        image = payload.image
        if image is None:
            raise ValueError("draft_annotation requires `image`")

        provider = context.resolve_provider(provider_name, role="multimodal")
        width, height = image_size(image)
        classes = self._require_classes(payload, params)
        prompt = payload.prompt or params.get("prompt") or self._build_prompt(width, height, classes)
        logger.info(
            "draft_annotation classes=%s prompt=%s",
            classes,
            prompt,
        )
        raw = provider.generate_json(
            prompt=prompt,
            image=image,
            system_prompt=(
                "You return strict JSON for image annotation. "
                "Use only allowed classes and keep label anchors close to the related box."
            ),
            temperature=float(params.get("temperature", 0.0)),
            max_tokens=int(params.get("max_tokens", 1024)),
            json_mode=bool(params.get("json_mode", False)),
            json_response_type=(
                str(params.get("json_response_type")).strip()
                if params.get("json_response_type") is not None
                else None
            ),
        )
        normalized = self._normalize_annotations(
            raw,
            width=width,
            height=height,
            allowed_classes=classes,
            min_class_match_score=float(params.get("class_match_score", 0.72)),
            max_label_distance_ratio=float(params.get("max_label_distance_ratio", 0.25)),
        )
        score_threshold = float(params.get("score_threshold", 0.0))
        annotations = [
            item
            for item in normalized
            if item.confidence is None or item.confidence >= score_threshold
        ]

        summary = raw.get("summary") if isinstance(raw, dict) else None
        return AnnotationResult(
            capability=self.name,
            provider=provider.name,
            image_width=width,
            image_height=height,
            annotations=annotations,
            summary=summary,
            raw=raw,
        )

    def _build_prompt(self, width: int, height: int, classes: list[str]) -> str:
        classes_repr = "[" + ", ".join(f'"{item}"' for item in classes) + "]"
        return (
            f"图像尺寸是 {width}x{height}。请做辅助标注草稿，只返回 JSON。\n"
            f"allowed_classes = {classes_repr}\n"
            "规则：\n"
            "1. label 只能从 allowed_classes 中选，不能发明新类目。\n"
            "2. 只标注图中真实可见且能明确判断类别的目标。\n"
            "3. bbox 使用原图像素坐标。\n"
            "4. label_anchor 是标签文字建议放置的位置，必须贴近对应 bbox，优先放在框的左上方或上方。\n"
            "5. 如果目标无法归入 allowed_classes，就不要返回它。\n"
            "JSON schema:\n"
            "{\n"
            '  "annotations": [\n'
            "    {\n"
            '      "label": "class-name",\n'
            '      "bbox": {"x1": 0, "y1": 0, "x2": 0, "y2": 0},\n'
            '      "label_anchor": {"x": 0, "y": 0},\n'
            '      "confidence": 0.0\n'
            "    }\n"
            "  ],\n"
            '  "summary": "optional short summary"\n'
            "}\n"
            "不要输出 markdown，不要解释。"
        )
