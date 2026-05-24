from __future__ import annotations

import logging
import uuid
from typing import Any

from models import AnnotationItem, AnnotationResult, TaskPayload
from storage import upload_bytes_to_s3
from utils import clamp, load_cv2_image, require_cv2
from .base import Capability, ProviderResolver, capability_metadata
from .draft import DraftAnnotationCapability

logger = logging.getLogger(__name__)


@capability_metadata(
    display_name="草稿标注预览",
    category="annotation",
    provider_role="multimodal",
    recommended_output_key="draft_preview",
    input_types=["image"],
    output_type="preview_image",
    scene_types=["assist_annotation"],
    parameter_fields=[
        {
            "key": "prompt",
            "label": "提示词",
            "widget": "textarea",
        },
        {
            "key": "class_match_score",
            "label": "类别匹配阈值",
            "value_type": "number",
            "widget": "number",
            "default_value": 0.72,
        },
        {
            "key": "score_threshold",
            "label": "置信度阈值",
            "value_type": "number",
            "widget": "number",
            "default_value": 0.2,
        },
        {
            "key": "preview_line_thickness",
            "label": "预览线宽",
            "value_type": "number",
            "widget": "number",
        },
        {
            "key": "preview_font_scale",
            "label": "预览字体缩放",
            "value_type": "number",
            "widget": "number",
        },
        {
            "key": "preview_s3_prefix",
            "label": "预览存储前缀",
            "widget": "text",
            "default_value": "auto_augment/draft_previews",
        },
    ],
)
class DraftAnnotationPreviewCapability(Capability):
    name = "draft_annotation_preview"
    description = "Directly draft bbox annotations with a multimodal model, then render an OpenCV preview image and upload it to S3."
    requires_provider = True

    def __init__(self) -> None:
        self._draft = DraftAnnotationCapability()

    def execute(
        self,
        payload: TaskPayload,
        params: dict[str, Any],
        context: ProviderResolver,
        provider_name: str | None = None,
    ) -> AnnotationResult:
        if payload.image is None:
            raise ValueError("draft_annotation_preview requires `image`")

        draft_result = self._draft.execute(
            payload=payload,
            params=params,
            context=context,
            provider_name=provider_name,
        )
        preview_bytes = self._render_preview(
            payload.image,
            draft_result.annotations,
            params=params,
        )
        s3_key = self._upload_preview(preview_bytes, params=params)
        summary = draft_result.summary or f"Generated {len(draft_result.annotations)} bbox annotations."

        logger.info(
            "draft_annotation_preview annotations=%s s3_key=%s",
            len(draft_result.annotations),
            s3_key,
        )

        return AnnotationResult(
            capability=self.name,
            provider=draft_result.provider,
            image_width=draft_result.image_width,
            image_height=draft_result.image_height,
            annotations=draft_result.annotations,
            summary=summary,
            raw={
                "draft_raw": draft_result.raw,
                "annotated_s3_key": s3_key,
                "annotated_object_count": len(draft_result.annotations),
            },
        )

    def _render_preview(
        self,
        image_payload,
        annotations: list[AnnotationItem],
        *,
        params: dict[str, Any],
    ) -> bytes:
        cv2 = require_cv2()
        canvas = load_cv2_image(image_payload).copy()
        image_height, image_width = canvas.shape[:2]
        min_side = max(1, min(image_width, image_height))
        line_thickness = max(2, int(params.get("preview_line_thickness", round(min_side / 400))))
        font_scale = float(params.get("preview_font_scale", max(0.6, min_side / 1200)))
        text_thickness = max(1, line_thickness - 1)
        font_face = cv2.FONT_HERSHEY_SIMPLEX

        for item in annotations:
            label = item.label.strip()
            bbox = item.bbox
            x1 = clamp(float(bbox["x1"]), 0, image_width - 1)
            y1 = clamp(float(bbox["y1"]), 0, image_height - 1)
            x2 = clamp(float(bbox["x2"]), 0, image_width - 1)
            y2 = clamp(float(bbox["y2"]), 0, image_height - 1)
            color = self._color_for_label(label)

            cv2.rectangle(canvas, (x1, y1), (x2, y2), color, line_thickness)

            if not label:
                continue

            anchor = item.label_anchor or {"x": x1 + 4, "y": max(0, y1 - 8)}
            text_x = clamp(float(anchor.get("x", x1 + 4)), 0, max(0, image_width - 2))
            text_y = clamp(float(anchor.get("y", max(0, y1 - 8))), 0, max(0, image_height - 2))
            text_x, text_y = self._normalize_text_origin(
                label,
                text_x=text_x,
                text_y=text_y,
                width=image_width,
                height=image_height,
                font_face=font_face,
                font_scale=font_scale,
                text_thickness=text_thickness,
            )
            (text_width, text_height), baseline = cv2.getTextSize(
                label,
                font_face,
                font_scale,
                text_thickness,
            )
            bg_left = max(0, text_x - 4)
            bg_top = max(0, text_y - text_height - baseline - 4)
            bg_right = min(image_width - 1, text_x + text_width + 4)
            bg_bottom = min(image_height - 1, text_y + baseline + 4)
            cv2.rectangle(canvas, (bg_left, bg_top), (bg_right, bg_bottom), color, -1)
            cv2.putText(
                canvas,
                label,
                (text_x, text_y),
                font_face,
                font_scale,
                (255, 255, 255),
                text_thickness,
                cv2.LINE_AA,
            )

        ok, encoded = cv2.imencode(".png", canvas)
        if not ok:
            raise ValueError("failed to encode annotated preview image")
        return encoded.tobytes()

    def _normalize_text_origin(
        self,
        label: str,
        *,
        text_x: int,
        text_y: int,
        width: int,
        height: int,
        font_face: int,
        font_scale: float,
        text_thickness: int,
    ) -> tuple[int, int]:
        cv2 = require_cv2()
        (text_width, text_height), baseline = cv2.getTextSize(
            label,
            font_face,
            font_scale,
            text_thickness,
        )
        normalized_x = clamp(text_x, 0, max(0, width - text_width - 6))
        min_y = text_height + baseline + 4
        max_y = max(min_y, height - baseline - 4)
        normalized_y = clamp(text_y, min_y, max_y)
        return normalized_x, normalized_y

    def _upload_preview(self, preview_bytes: bytes, *, params: dict[str, Any]) -> str:
        prefix = str(params.get("preview_s3_prefix") or "auto_augment/draft_previews").strip().strip("/")
        s3_key = f"{prefix}/{uuid.uuid4().hex}.png"
        upload_bytes_to_s3(preview_bytes, s3_key)
        return s3_key

    def _color_for_label(self, label: str) -> tuple[int, int, int]:
        palette = [
            (52, 152, 219),
            (46, 204, 113),
            (231, 76, 60),
            (241, 196, 15),
            (155, 89, 182),
            (26, 188, 156),
            (230, 126, 34),
            (149, 165, 166),
        ]
        if not label:
            return palette[0]
        index = sum(ord(char) for char in label) % len(palette)
        return palette[index]
