from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from models import (
    AnnotationItem,
    AnnotationResult,
    CapabilityDescriptor,
    DescriptionResult,
    OverlayRenderResult,
    TaskPayload,
)
from ocr import OCRTextLine, RapidOCRService, normalize_label_to_allowed_classes
from utils import clamp, image_size, load_cv2_image, require_cv2

BoxTuple = tuple[int, int, int, int]


class ProviderResolver(Protocol):
    def resolve_provider(self, explicit_name: str | None = None, role: str = "multimodal") -> Any:
        ...


class Capability(ABC):
    name: str
    description: str
    requires_provider: bool = False

    def describe(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            name=self.name,
            description=self.description,
            requires_provider=self.requires_provider,
        )

    @abstractmethod
    def execute(
        self,
        payload: TaskPayload,
        params: dict[str, Any],
        context: ProviderResolver,
        provider_name: str | None = None,
    ) -> Any:
        raise NotImplementedError


class AnnotationNormalizationMixin:
    def _require_classes(self, payload: TaskPayload, params: dict[str, Any]) -> list[str]:
        classes = payload.classes or params.get("classes", [])
        cleaned = [str(item).strip() for item in classes if str(item).strip()]
        if not cleaned:
            raise ValueError(
                "annotation extraction requires non-empty `classes`; free-form labels are disabled")
        return cleaned

    def _normalize_annotations(
        self,
        raw: dict[str, Any] | list[Any],
        *,
        width: int,
        height: int,
        allowed_classes: list[str],
        min_class_match_score: float,
        max_label_distance_ratio: float,
    ) -> list[AnnotationItem]:
        if isinstance(raw, list):
            records = raw
        else:
            records = raw.get("annotations", [])

        normalized: list[AnnotationItem] = []
        for item in records:
            if not isinstance(item, dict):
                continue
            label = normalize_label_to_allowed_classes(
                str(item.get("label") or item.get("name") or "").strip(),
                allowed_classes,
                min_score=min_class_match_score,
            )
            if not label:
                continue
            bbox = item.get("bbox") or item.get("box") or {}
            x1, y1, x2, y2 = self._extract_box(
                bbox, width=width, height=height)
            if x2 <= x1 or y2 <= y1:
                continue
            label_anchor = self._extract_label_anchor(
                item.get("label_anchor") or item.get(
                    "label_position") or item.get("text_position"),
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                width=width,
                height=height,
                max_distance_ratio=max_label_distance_ratio,
            )
            confidence = item.get("confidence")
            normalized.append(
                AnnotationItem(
                    label=label,
                    bbox={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    label_anchor=label_anchor,
                    confidence=float(
                        confidence) if confidence is not None else None,
                    source=getattr(self, "name", None),
                )
            )
        return normalized

    def _extract_box(self, bbox: dict[str, Any], *, width: int, height: int) -> BoxTuple:
        keys = ("x1", "y1", "x2", "y2")
        if all(key in bbox for key in keys):
            values = [float(bbox[key]) for key in keys]
        else:
            alt_keys = ("left", "top", "right", "bottom")
            values = [float(bbox.get(key, 0)) for key in alt_keys]

        scaled = self._scale_if_normalized(values, width=width, height=height)
        x1 = clamp(scaled[0], 0, width)
        y1 = clamp(scaled[1], 0, height)
        x2 = clamp(scaled[2], 0, width)
        y2 = clamp(scaled[3], 0, height)
        return x1, y1, x2, y2

    def _scale_if_normalized(
        self, values: list[float], *, width: int, height: int
    ) -> tuple[float, float, float, float]:
        if values and max(values) <= 1.0:
            return (
                values[0] * width,
                values[1] * height,
                values[2] * width,
                values[3] * height,
            )
        return values[0], values[1], values[2], values[3]

    def _extract_label_anchor(
        self,
        raw_anchor: Any,
        *,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        width: int,
        height: int,
        max_distance_ratio: float,
    ) -> dict[str, int]:
        default_anchor = self._default_label_anchor(
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            width=width,
            height=height,
        )
        if not isinstance(raw_anchor, dict):
            return default_anchor

        raw_x = raw_anchor.get("x", raw_anchor.get("left"))
        raw_y = raw_anchor.get("y", raw_anchor.get("top"))
        if raw_x is None or raw_y is None:
            return default_anchor

        anchor_x = float(raw_x)
        anchor_y = float(raw_y)
        if max(anchor_x, anchor_y) <= 1.0:
            anchor_x *= width
            anchor_y *= height

        point = {
            "x": clamp(anchor_x, 0, width),
            "y": clamp(anchor_y, 0, height),
        }
        if not self._is_anchor_close_to_box(
            point,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            max_distance=max(20, int(min(width, height) * max_distance_ratio)),
        ):
            return default_anchor
        return point

    def _default_label_anchor(
        self, *, x1: int, y1: int, x2: int, y2: int, width: int, height: int
    ) -> dict[str, int]:
        vertical_padding = 8
        horizontal_padding = 4
        candidate_y = y1 - vertical_padding
        if candidate_y < 0:
            candidate_y = min(height, y2 + 18)
        return {
            "x": clamp(x1 + horizontal_padding, 0, width),
            "y": clamp(candidate_y, 0, height),
        }

    def _is_anchor_close_to_box(
        self,
        anchor: dict[str, int],
        *,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        max_distance: int,
    ) -> bool:
        nearest_x = min(max(anchor["x"], x1), x2)
        nearest_y = min(max(anchor["y"], y1), y2)
        distance_x = anchor["x"] - nearest_x
        distance_y = anchor["y"] - nearest_y
        return distance_x * distance_x + distance_y * distance_y <= max_distance * max_distance

    def _area(self, box: BoxTuple) -> int:
        return max(0, box[2] - box[0]) * max(0, box[3] - box[1])

    def _iou(self, left: BoxTuple, right: BoxTuple) -> float:
        ix1 = max(left[0], right[0])
        iy1 = max(left[1], right[1])
        ix2 = min(left[2], right[2])
        iy2 = min(left[3], right[3])
        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        if inter == 0:
            return 0.0
        union = self._area(left) + self._area(right) - inter
        return inter / union if union else 0.0


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
            raise ValueError(
                "describe_image requires `image` or `overlay_image`")

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
        prompt = payload.prompt or params.get(
            "prompt") or self._build_prompt(width, height, classes)
        raw = provider.generate_json(
            prompt=prompt,
            image=image,
            system_prompt=(
                "You return strict JSON for image annotation. "
                "Use only allowed classes and keep label anchors close to the related box."
            ),
            temperature=float(params.get("temperature", 0.0)),
            max_tokens=int(params.get("max_tokens", 1024)),
        )
        normalized = self._normalize_annotations(
            raw,
            width=width,
            height=height,
            allowed_classes=classes,
            min_class_match_score=float(params.get("class_match_score", 0.72)),
            max_label_distance_ratio=float(
                params.get("max_label_distance_ratio", 0.25)),
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


class RenderWhiteAnnotationOverlayCapability(Capability):
    name = "render_white_annotation_overlay"
    description = "Use an image editing model to draw pure white boxes and labels for allowed classes."
    requires_provider = True

    def execute(
        self,
        payload: TaskPayload,
        params: dict[str, Any],
        context: ProviderResolver,
        provider_name: str | None = None,
    ) -> OverlayRenderResult:
        image = payload.image
        if image is None:
            raise ValueError(
                "render_white_annotation_overlay requires `image`")

        classes = [item.strip() for item in payload.classes if item.strip()]
        if not classes:
            raise ValueError(
                "render_white_annotation_overlay requires non-empty `classes`")

        provider = context.resolve_provider(provider_name, role="image_edit")
        edit_prompt = payload.prompt or params.get("prompt")
        image_dimensions: dict[str, int] | None = None
        if edit_prompt is None:
            width, height = image_size(image)
            image_dimensions = {"width": width, "height": height}
            edit_prompt = self._build_edit_prompt(width, height, classes)
        overlay_image = provider.edit_image(
            prompt=edit_prompt,
            image=image,
            size=params.get("size"),
            background=params.get("background"),
        )
        return OverlayRenderResult(
            capability=self.name,
            provider=provider.name,
            overlay_image=overlay_image,
            edit_prompt=edit_prompt,
            classes=classes,
            summary="Generated white-box overlay image for downstream annotation extraction.",
            raw={"image_size": image_dimensions} if image_dimensions is not None else None,
        )

    def _build_edit_prompt(self, width: int, height: int, classes: list[str]) -> str:
        allowed = "[" + ", ".join(f'"{item}"' for item in classes) + "]"
        return (
            f"Edit this image for annotation assistance. The image size is {width}x{height}.\n"
            f"allowed_classes = {allowed}\n"
            "Instructions:\n"
            "1. Only annotate objects that clearly belong to allowed_classes.\n"
            "2. Draw each annotation as a pure white rectangular box using #FFFFFF.\n"
            "3. Draw one pure white class label near each box, preferably at the upper-left or directly above the box.\n"
            "4. The label text must be exactly one item from allowed_classes.\n"
            "5. Keep the original image content unchanged except for the white boxes and white labels.\n"
            "6. Do not add any extra legend, explanation, watermark, arrows, or decorative marks.\n"
            "7. If an object cannot be confidently mapped to allowed_classes, do not annotate it.\n"
            "8. If boxes overlap, still draw every visible box separately.\n"
            "Return only the edited image."
        )


class UnderstandWhiteAnnotationsCapability(AnnotationNormalizationMixin, Capability):
    name = "understand_white_annotations"
    description = "Use a multimodal model to recover boxes and labels from a white-box overlay image."
    requires_provider = True

    def execute(
        self,
        payload: TaskPayload,
        params: dict[str, Any],
        context: ProviderResolver,
        provider_name: str | None = None,
    ) -> AnnotationResult:
        image = payload.overlay_image or payload.image
        if image is None:
            raise ValueError(
                "understand_white_annotations requires `overlay_image` or `image`")

        provider = context.resolve_provider(provider_name, role="multimodal")
        width, height = image_size(image)
        classes = self._require_classes(payload, params)
        prompt = (
            payload.prompt
            or params.get("prompt")
            or self._build_overlay_prompt(width, height, classes)
        )
        raw = provider.generate_json(
            prompt=prompt,
            image=image,
            system_prompt=(
                "You recover annotation metadata from a white-box overlay image. "
                "Do not infer hidden objects. Read only visible white boxes and nearby white labels."
            ),
            temperature=float(params.get("temperature", 0.0)),
            max_tokens=int(params.get("max_tokens", 1024)),
        )
        annotations = self._normalize_annotations(
            raw,
            width=width,
            height=height,
            allowed_classes=classes,
            min_class_match_score=float(params.get("class_match_score", 0.72)),
            max_label_distance_ratio=float(
                params.get("max_label_distance_ratio", 0.25)),
        )
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

    def _build_overlay_prompt(self, width: int, height: int, classes: list[str]) -> str:
        classes_repr = "[" + ", ".join(f'"{item}"' for item in classes) + "]"
        return (
            f"图像尺寸是 {width}x{height}。这是一张已经画好纯白色标注框和纯白色类别文字的叠加图。\n"
            f"allowed_classes = {classes_repr}\n"
            "请根据白色矩形框和离框最近的白色标签文字，还原结构化标注，只返回 JSON。\n"
            "规则：\n"
            "1. 一个白色矩形框对应一个 annotation。\n"
            "2. label 只能从 allowed_classes 中选。\n"
            "3. 如果多个框重叠，仍然要把每个可见框单独返回。\n"
            "4. label_anchor 是图中该标签文字实际所在的大致位置，必须靠近对应框。\n"
            "5. 如果某段文字无法明确归属某个框，不要强行关联。\n"
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


class ExtractWhiteAnnotationsCapability(AnnotationNormalizationMixin, Capability):
    name = "extract_white_annotations"
    description = "Use OpenCV to detect white boxes, then assign OCR text to the nearest box."
    requires_provider = False

    def __init__(self) -> None:
        self.ocr = RapidOCRService()

    def execute(
        self,
        payload: TaskPayload,
        params: dict[str, Any],
        context: ProviderResolver,
        provider_name: str | None = None,
    ) -> AnnotationResult:
        image_payload = payload.overlay_image or payload.image
        if image_payload is None:
            raise ValueError(
                "extract_white_annotations requires `overlay_image` or `image`")

        cv2 = require_cv2()
        image = load_cv2_image(image_payload)
        image_height, image_width = image.shape[:2]
        threshold = int(params.get("white_threshold", 235))
        min_area = int(params.get("min_area", 300))
        min_width = int(params.get("min_width", 20))
        min_height = int(params.get("min_height", 20))
        kernel_size = int(params.get("kernel_size", 3))
        line_scale = int(params.get("line_scale", 30))
        infer_labels = bool(params.get("infer_labels", True))
        max_candidates = int(params.get("max_candidates", 200))
        classes = [item.strip() for item in payload.classes if item.strip()]
        min_match_score = float(params.get("class_match_score", 0.6))
        border_density_threshold = float(
            params.get("border_density_threshold", 0.12))
        max_text_distance = int(
            params.get(
                "max_text_distance",
                max(30, int(min(image_width, image_height) *
                    float(params.get("max_text_distance_ratio", 0.12)))),
            )
        )

        boxes = self._detect_boxes(
            image=image,
            threshold=threshold,
            min_area=min_area,
            min_width=min_width,
            min_height=min_height,
            kernel_size=kernel_size,
            line_scale=line_scale,
            border_density_threshold=border_density_threshold,
            max_candidates=max_candidates,
        )

        text_items: list[OCRTextLine] = []
        if infer_labels:
            text_items = self.ocr.detect_lines(
                image,
                allowed_classes=classes,
                min_match_score=min_match_score,
            )

        assignments = self._assign_text_lines_to_boxes(
            boxes,
            text_items,
            image_width=image_width,
            image_height=image_height,
            max_text_distance=max_text_distance,
        )

        annotations: list[AnnotationItem] = []
        for index, (x1, y1, x2, y2) in enumerate(boxes):
            matched_text = assignments.get(index)
            label = matched_text.text if matched_text is not None else ""
            label_anchor = self._default_label_anchor(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                width=image_width,
                height=image_height,
            )
            if matched_text is not None:
                label_anchor = self._extract_label_anchor(
                    {"x": matched_text.bbox["x1"],
                        "y": matched_text.bbox["y1"]},
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    width=image_width,
                    height=image_height,
                    max_distance_ratio=max_text_distance /
                    max(1, min(image_width, image_height)),
                )

            annotations.append(
                AnnotationItem(
                    label=label,
                    bbox={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    label_anchor=label_anchor,
                    confidence=matched_text.score if matched_text is not None else None,
                    source=self.name,
                )
            )

        return AnnotationResult(
            capability=self.name,
            provider="rapidocr" if infer_labels else None,
            image_width=image_width,
            image_height=image_height,
            annotations=annotations,
            summary=f"Extracted {len(annotations)} white annotation boxes and matched {len(assignments)} text labels.",
            raw={
                "box_count": len(boxes),
                "text_count": len(text_items),
                "matched_text_count": len(assignments),
            },
        )

    def _detect_boxes(
        self,
        *,
        image: Any,
        threshold: int,
        min_area: int,
        min_width: int,
        min_height: int,
        kernel_size: int,
        line_scale: int,
        border_density_threshold: float,
        max_candidates: int,
    ) -> list[BoxTuple]:
        cv2 = require_cv2()
        mask = cv2.inRange(image, (threshold, threshold,
                           threshold), (255, 255, 255))
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (kernel_size, kernel_size))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        line_mask = self._extract_line_mask(mask, line_scale=line_scale)
        contours, _ = cv2.findContours(
            line_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        candidates: list[BoxTuple] = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w * h < min_area or w < min_width or h < min_height:
                continue
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
            if len(approx) < 4 or len(approx) > 16:
                continue

            rect_area = max(1, w * h)
            fill_ratio = cv2.contourArea(contour) / rect_area
            if fill_ratio > 0.75:
                continue

            roi = line_mask[y: y + h, x: x + w]
            if not self._looks_like_box_frame(roi, border_density_threshold=border_density_threshold):
                continue
            candidates.append((x, y, x + w, y + h))

        return self._deduplicate_boxes(candidates)[:max_candidates]

    def _extract_line_mask(self, mask: Any, *, line_scale: int) -> Any:
        cv2 = require_cv2()
        height, width = mask.shape[:2]
        horizontal_size = max(10, width // max(2, line_scale))
        vertical_size = max(10, height // max(2, line_scale))
        horizontal_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (horizontal_size, 1))
        vertical_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (1, vertical_size))

        horizontal = cv2.morphologyEx(mask, cv2.MORPH_OPEN, horizontal_kernel)
        vertical = cv2.morphologyEx(mask, cv2.MORPH_OPEN, vertical_kernel)
        line_mask = cv2.bitwise_or(horizontal, vertical)
        return cv2.dilate(
            line_mask,
            cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)),
            iterations=1,
        )

    def _looks_like_box_frame(self, roi: Any, *, border_density_threshold: float) -> bool:
        if roi.size == 0:
            return False

        height, width = roi.shape[:2]
        border_thickness = max(1, min(height, width) // 20)
        top = self._nonzero_ratio(roi[:border_thickness, :])
        bottom = self._nonzero_ratio(
            roi[max(0, height - border_thickness):, :])
        left = self._nonzero_ratio(roi[:, :border_thickness])
        right = self._nonzero_ratio(roi[:, max(0, width - border_thickness):])

        has_horizontal = top >= border_density_threshold or bottom >= border_density_threshold
        has_vertical = left >= border_density_threshold or right >= border_density_threshold
        dense_sides = sum(
            value >= border_density_threshold for value in (top, bottom, left, right)
        )
        return has_horizontal and has_vertical and dense_sides >= 3

    def _nonzero_ratio(self, region: Any) -> float:
        if region.size == 0:
            return 0.0
        cv2 = require_cv2()
        return float(cv2.countNonZero(region)) / float(region.size)

    def _deduplicate_boxes(self, boxes: list[BoxTuple]) -> list[BoxTuple]:
        selected: list[BoxTuple] = []
        for candidate in sorted(boxes, key=self._area, reverse=True):
            if any(self._is_duplicate_box(candidate, existing) for existing in selected):
                continue
            selected.append(candidate)
        return sorted(selected, key=lambda item: (item[1], item[0]))

    def _is_duplicate_box(self, left: BoxTuple, right: BoxTuple) -> bool:
        edge_tolerance = 8
        if all(abs(left[index] - right[index]) <= edge_tolerance for index in range(4)):
            return True
        iou = self._iou(left, right)
        if iou >= 0.92:
            return True
        if self._contains(left, right, margin=edge_tolerance) or self._contains(right, left, margin=edge_tolerance):
            smaller = min(self._area(left), self._area(right))
            larger = max(self._area(left), self._area(right))
            if larger and (smaller / larger) >= 0.88:
                return True
        return False

    def _contains(self, outer: BoxTuple, inner: BoxTuple, *, margin: int) -> bool:
        return (
            outer[0] - margin <= inner[0]
            and outer[1] - margin <= inner[1]
            and outer[2] + margin >= inner[2]
            and outer[3] + margin >= inner[3]
        )

    def _assign_text_lines_to_boxes(
        self,
        boxes: list[BoxTuple],
        text_items: list[OCRTextLine],
        *,
        image_width: int,
        image_height: int,
        max_text_distance: int,
    ) -> dict[int, OCRTextLine]:
        pair_scores: list[tuple[float, int, int]] = []
        for box_index, box in enumerate(boxes):
            for text_index, text_item in enumerate(text_items):
                score = self._score_text_for_box(
                    box,
                    text_item,
                    image_width=image_width,
                    image_height=image_height,
                    max_text_distance=max_text_distance,
                )
                if score is None:
                    continue
                pair_scores.append((score, box_index, text_index))

        assignments: dict[int, OCRTextLine] = {}
        used_text_indexes: set[int] = set()
        for _, box_index, text_index in sorted(pair_scores, key=lambda item: item[0]):
            if box_index in assignments or text_index in used_text_indexes:
                continue
            assignments[box_index] = text_items[text_index]
            used_text_indexes.add(text_index)
        return assignments

    def _score_text_for_box(
        self,
        box: BoxTuple,
        text_item: OCRTextLine,
        *,
        image_width: int,
        image_height: int,
        max_text_distance: int,
    ) -> float | None:
        x1, y1, x2, y2 = box
        tx1 = text_item.bbox["x1"]
        ty1 = text_item.bbox["y1"]
        tx2 = text_item.bbox["x2"]
        ty2 = text_item.bbox["y2"]

        if self._iou(box, (tx1, ty1, tx2, ty2)) > 0.2:
            return None

        anchor = self._default_label_anchor(
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            width=image_width,
            height=image_height,
        )
        text_center_x, text_center_y = text_item.center

        anchor_distance = abs(
            text_center_x - anchor["x"]) + abs(text_center_y - anchor["y"])
        box_distance = self._distance_to_box(box, text_item.center)
        distance = min(anchor_distance, box_distance)
        if distance > max_text_distance:
            return None

        penalty = 0.0
        if text_center_y > y2:
            penalty += max_text_distance * 0.35
        elif y1 <= text_center_y <= y2:
            penalty += max_text_distance * 0.6

        if text_center_x < x1:
            penalty += min(abs(text_center_x - x1), max_text_distance) * 0.1
        elif text_center_x > x2:
            penalty += min(abs(text_center_x - x2), max_text_distance) * 0.1

        return float(distance + penalty)

    def _distance_to_box(self, box: BoxTuple, point: tuple[int, int]) -> int:
        x1, y1, x2, y2 = box
        point_x, point_y = point
        nearest_x = min(max(point_x, x1), x2)
        nearest_y = min(max(point_y, y1), y2)
        return abs(point_x - nearest_x) + abs(point_y - nearest_y)


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
        min_annotation_count = int(params.get(
            "assist_min_annotation_count", 1))
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
