"""Helpers for storing and loading annotation record payloads."""
import json
from typing import Any

from app.common.constants import AnnotationType


def build_annotation_record_object_key(
    annotation_save_path: str,
    sample_item_id: int,
    annotation_type: int,
) -> str:
    return f"{annotation_save_path}/records/{sample_item_id}{get_annotation_record_extension(annotation_type)}"


def get_annotation_record_extension(annotation_type: int) -> str:
    if annotation_type in {AnnotationType.LLM, AnnotationType.MLLM}:
        return ".json"
    return ".txt"


def serialize_annotation_record_payload(
    annotation_type: int,
    content: dict[str, Any],
) -> tuple[bytes, str]:
    if annotation_type in {AnnotationType.LLM, AnnotationType.MLLM}:
        return json.dumps(content, ensure_ascii=False, indent=2).encode("utf-8"), "application/json"

    if annotation_type == AnnotationType.CLASSIFICATION:
        return _serialize_classification_payload(content).encode("utf-8"), "text/plain"

    return _extract_label_text(content).encode("utf-8"), "text/plain"


def parse_annotation_record_payload(
    annotation_type: int,
    raw_payload: Any,
    source_path: str | None = None,
) -> dict[str, Any]:
    if raw_payload is None:
        return {}
    if isinstance(raw_payload, dict):
        return raw_payload

    if isinstance(raw_payload, bytes):
        text = raw_payload.decode("utf-8")
    else:
        text = str(raw_payload)

    if _should_parse_as_json(annotation_type, source_path):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {"value": parsed}

    if annotation_type == AnnotationType.CLASSIFICATION:
        return {
            "format": "classification",
            "class_ids": _parse_classification_ids(text),
        }

    return {
        "format": "yolo",
        "label_text": text,
    }


def is_annotation_record_storage_path(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return value.startswith("annotations/") and value.rsplit("/", 1)[-1].count(".") == 1


def _should_parse_as_json(annotation_type: int, source_path: str | None) -> bool:
    if annotation_type in {AnnotationType.LLM, AnnotationType.MLLM}:
        return True
    return bool(source_path and source_path.endswith(".json"))


def _extract_label_text(content: dict[str, Any]) -> str:
    direct = content.get("label_text") or content.get("yolo") or content.get("content")
    return direct if isinstance(direct, str) else ""


def _serialize_classification_payload(content: dict[str, Any]) -> str:
    class_ids = _normalize_classification_ids(content.get("class_ids"))
    if not class_ids:
        return ""
    if len(class_ids) == 1:
        return str(class_ids[0])
    return json.dumps(class_ids, ensure_ascii=False)


def _parse_classification_ids(text: str) -> list[int]:
    normalized = text.strip()
    if not normalized:
        return []

    try:
        parsed = json.loads(normalized)
    except json.JSONDecodeError:
        return _normalize_classification_ids(normalized.replace(",", " ").split())

    if isinstance(parsed, list):
        return _normalize_classification_ids(parsed)
    if isinstance(parsed, (int, str)):
        return _normalize_classification_ids([parsed])
    if isinstance(parsed, dict):
        return _normalize_classification_ids(parsed.get("class_ids"))
    return []


def _normalize_classification_ids(values: Any) -> list[int]:
    if not isinstance(values, list):
        values = [values] if values is not None else []

    normalized: list[int] = []
    seen: set[int] = set()
    for value in values:
        try:
            class_id = int(str(value).strip())
        except (TypeError, ValueError):
            continue
        if class_id < 0 or class_id in seen:
            continue
        seen.add(class_id)
        normalized.append(class_id)
    normalized.sort()
    return normalized
