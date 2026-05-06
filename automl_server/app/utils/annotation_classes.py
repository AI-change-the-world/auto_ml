"""Helpers for annotation class name parsing."""
import json
import re
from typing import Iterable, Optional


CLASS_DELIMITER_PATTERN = re.compile(r"[,;\n\r；，]+")


def _normalize_items(items: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    classes: list[str] = []

    for item in items:
        class_name = str(item).strip()
        if not class_name or class_name in seen:
            continue
        seen.add(class_name)
        classes.append(class_name)

    return classes


def parse_annotation_classes(raw_classes: Optional[str]) -> list[str]:
    if not raw_classes:
        return []

    try:
        parsed = json.loads(raw_classes)
        if isinstance(parsed, list):
            return _normalize_items(parsed)
        if isinstance(parsed, str):
            return _normalize_items(CLASS_DELIMITER_PATTERN.split(parsed))
    except Exception:
        return _normalize_items(CLASS_DELIMITER_PATTERN.split(raw_classes))

    return []


def serialize_annotation_classes(raw_classes: Optional[str]) -> str:
    classes = parse_annotation_classes(raw_classes)
    return json.dumps(classes, ensure_ascii=False)
