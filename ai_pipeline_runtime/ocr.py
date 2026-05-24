from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any


@dataclass
class OCRTextLine:
    text: str
    raw_text: str
    score: float | None
    bbox: dict[str, int]

    @property
    def center(self) -> tuple[int, int]:
        return (
            int((self.bbox["x1"] + self.bbox["x2"]) / 2),
            int((self.bbox["y1"] + self.bbox["y2"]) / 2),
        )


def require_rapidocr():
    try:
        from rapidocr import RapidOCR
    except ImportError as exc:
        raise RuntimeError(
            "rapidocr and onnxruntime are required for OCR features"
        ) from exc
    return RapidOCR


def normalize_label_to_allowed_classes(
    label: str,
    allowed_classes: list[str],
    *,
    min_score: float = 0.6,
) -> str:
    cleaned = _normalize_text(label)
    if not cleaned:
        return ""
    if not allowed_classes:
        return label.strip()

    normalized_map = {_normalize_text(item): item for item in allowed_classes}
    exact = normalized_map.get(cleaned)
    if exact:
        return exact

    best_label = ""
    best_score = 0.0
    for item in allowed_classes:
        normalized_item = _normalize_text(item)
        if not normalized_item:
            continue
        if cleaned in normalized_item or normalized_item in cleaned:
            return item
        score = SequenceMatcher(None, cleaned, normalized_item).ratio()
        if score > best_score:
            best_score = score
            best_label = item

    if best_score >= min_score:
        return best_label
    return ""


class RapidOCRService:
    def __init__(self) -> None:
        self._engine: Any | None = None

    @property
    def engine(self) -> Any:
        if self._engine is None:
            rapidocr_cls = require_rapidocr()
            self._engine = rapidocr_cls()
        return self._engine

    def recognize(
        self,
        image: Any,
        *,
        allowed_classes: list[str] | None = None,
        min_match_score: float = 0.6,
    ) -> str:
        lines = self.detect_lines(
            image,
            allowed_classes=allowed_classes,
            min_match_score=min_match_score,
        )
        return " ".join(item.text for item in lines if item.text).strip()

    def detect_lines(
        self,
        image: Any,
        *,
        allowed_classes: list[str] | None = None,
        min_match_score: float = 0.6,
    ) -> list[OCRTextLine]:
        result = self.engine(image)
        return self._extract_lines(
            result,
            allowed_classes=allowed_classes or [],
            min_match_score=min_match_score,
        )

    def _extract_lines(
        self,
        result: Any,
        *,
        allowed_classes: list[str],
        min_match_score: float,
    ) -> list[OCRTextLine]:
        if result is None:
            return []

        if hasattr(result, "boxes") and hasattr(result, "txts"):
            boxes = self._coerce_sequence(getattr(result, "boxes", None))
            texts = self._coerce_sequence(getattr(result, "txts", None))
            scores = self._coerce_sequence(getattr(result, "scores", None))
            return self._build_lines(
                boxes,
                texts,
                scores,
                allowed_classes=allowed_classes,
                min_match_score=min_match_score,
            )

        if isinstance(result, tuple):
            for item in result:
                extracted = self._extract_lines(
                    item,
                    allowed_classes=allowed_classes,
                    min_match_score=min_match_score,
                )
                if extracted:
                    return extracted
            return []

        if isinstance(result, list):
            # Common shape: [[box, text, score], ...]
            if result and all(isinstance(item, (list, tuple)) and len(item) >= 2 for item in result):
                boxes: list[Any] = []
                texts: list[str] = []
                scores: list[float | None] = []
                for item in result:
                    boxes.append(item[0])
                    texts.append(self._extract_text_value(item[1]))
                    scores.append(self._extract_score_value(item))
                return self._build_lines(
                    boxes,
                    texts,
                    scores,
                    allowed_classes=allowed_classes,
                    min_match_score=min_match_score,
                )
            return []

        return []

    def _build_lines(
        self,
        boxes: list[Any],
        texts: list[Any],
        scores: list[Any],
        *,
        allowed_classes: list[str],
        min_match_score: float,
    ) -> list[OCRTextLine]:
        lines: list[OCRTextLine] = []
        for index, raw_text in enumerate(texts):
            text = str(raw_text).strip() if raw_text is not None else ""
            if not text:
                continue
            normalized_text = (
                normalize_label_to_allowed_classes(
                    text,
                    allowed_classes,
                    min_score=min_match_score,
                )
                if allowed_classes
                else text
            )
            if allowed_classes and not normalized_text:
                continue

            bbox = self._to_bbox(boxes[index] if index < len(boxes) else None)
            if bbox is None:
                continue

            score = None
            if index < len(scores) and scores[index] is not None:
                try:
                    score = float(scores[index])
                except (TypeError, ValueError):
                    score = None

            lines.append(
                OCRTextLine(
                    text=normalized_text,
                    raw_text=text,
                    score=score,
                    bbox=bbox,
                )
            )
        return lines

    def _coerce_sequence(self, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, str):
            return [value]
        if hasattr(value, "tolist"):
            converted = value.tolist()
            if converted is None:
                return []
            if isinstance(converted, list):
                return converted
            if isinstance(converted, tuple):
                return list(converted)
            return [converted]
        try:
            return list(value)
        except TypeError:
            return [value]

    def _extract_text_value(self, value: Any) -> str:
        if isinstance(value, tuple):
            return str(value[0])
        return str(value)

    def _extract_score_value(self, item: list[Any] | tuple[Any, ...]) -> float | None:
        if len(item) >= 3:
            try:
                return float(item[2])
            except (TypeError, ValueError):
                return None
        text_value = item[1]
        if isinstance(text_value, tuple) and len(text_value) >= 2:
            try:
                return float(text_value[1])
            except (TypeError, ValueError):
                return None
        return None

    def _to_bbox(self, raw_box: Any) -> dict[str, int] | None:
        if raw_box is None:
            return None
        if hasattr(raw_box, "tolist"):
            raw_box = raw_box.tolist()
        if isinstance(raw_box, dict):
            if {"x1", "y1", "x2", "y2"} <= set(raw_box.keys()):
                return {
                    "x1": int(raw_box["x1"]),
                    "y1": int(raw_box["y1"]),
                    "x2": int(raw_box["x2"]),
                    "y2": int(raw_box["y2"]),
                }
            return None

        if isinstance(raw_box, (list, tuple)) and raw_box:
            if len(raw_box) == 4 and all(isinstance(item, (int, float)) for item in raw_box):
                x1, y1, x2, y2 = raw_box
                return {
                    "x1": int(min(x1, x2)),
                    "y1": int(min(y1, y2)),
                    "x2": int(max(x1, x2)),
                    "y2": int(max(y1, y2)),
                }

            points: list[tuple[float, float]] = []
            for item in raw_box:
                if (
                    isinstance(item, (list, tuple))
                    and len(item) >= 2
                    and isinstance(item[0], (int, float))
                    and isinstance(item[1], (int, float))
                ):
                    points.append((float(item[0]), float(item[1])))
            if points:
                xs = [point[0] for point in points]
                ys = [point[1] for point in points]
                return {
                    "x1": int(min(xs)),
                    "y1": int(min(ys)),
                    "x2": int(max(xs)),
                    "y2": int(max(ys)),
                }
        return None


def _normalize_text(text: str) -> str:
    return "".join(char.lower() for char in text if char.isalnum())
