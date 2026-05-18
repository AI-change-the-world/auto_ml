from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from models import AnnotationItem, CapabilityDescriptor, TaskPayload
from ocr import normalize_label_to_allowed_classes
from utils import clamp

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
                "annotation extraction requires non-empty `classes`; free-form labels are disabled"
            )
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
            x1, y1, x2, y2 = self._extract_box(bbox, width=width, height=height)
            if x2 <= x1 or y2 <= y1:
                continue
            label_anchor = self._extract_label_anchor(
                item.get("label_anchor") or item.get("label_position") or item.get("text_position"),
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
                    confidence=float(confidence) if confidence is not None else None,
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
        self,
        values: list[float],
        *,
        width: int,
        height: int,
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
        self,
        *,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        width: int,
        height: int,
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
