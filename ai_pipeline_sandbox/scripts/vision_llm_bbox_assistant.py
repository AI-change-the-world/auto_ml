"""OpenAI-compatible vision LLM batch assistant for detection annotations."""
from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MAX_IMAGE_BYTES = 20 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 120


def _parse_classes(value: Any) -> list[str]:
    if isinstance(value, list):
        candidates = value
    else:
        raw_value = str(value or "").strip()
        try:
            parsed = json.loads(raw_value)
            candidates = parsed if isinstance(parsed, list) else re.split(r"[,;\n\r；，]+", raw_value)
        except json.JSONDecodeError:
            candidates = re.split(r"[,;\n\r；，]+", raw_value)
    classes: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        name = str(candidate).strip()
        if name and name not in seen:
            classes.append(name)
            seen.add(name)
    return classes


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/chat/completions"
    return f"{normalized}/v1/chat/completions"


def _build_prompt(classes: list[str], extra_prompt: str) -> str:
    prompt = (
        "You are an image object detection annotator. Detect only objects belonging to these allowed "
        f"classes: {', '.join(classes)}. Return JSON only, with this exact shape: "
        '{"detections":[{"class_name":"allowed class name","bbox":[x1,y1,x2,y2]}]}. '
        "bbox must use xyxy coordinates normalized to integers from 0 to 1000. "
        "Do not use markdown. Return an empty detections array when no allowed object is visible."
    )
    return f"{prompt}\nAdditional requirements: {extra_prompt.strip()}" if extra_prompt.strip() else prompt


def _image_data_url(local_path: str) -> str:
    image_path = Path(local_path)
    data = image_path.read_bytes()
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("image exceeds the 20 MB vision request limit")
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    return f"data:{mime_type};base64,{base64.b64encode(data).decode('ascii')}"


def _extract_response_content(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("vision API returned no choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(part.get("text") or "")
            for part in content
            if isinstance(part, dict)
        )
    raise ValueError("vision API returned no message content")


def _decode_json_content(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("vision API response must be a JSON object")
    return payload


def _to_yolo_labels(payload: dict[str, Any], classes: list[str]) -> str:
    detections = payload.get("detections")
    if not isinstance(detections, list):
        raise ValueError("vision API response must contain a detections array")
    class_indices = {name.casefold(): index for index, name in enumerate(classes)}
    labels: list[str] = []
    for detection in detections:
        if not isinstance(detection, dict):
            continue
        class_name = str(detection.get("class_name") or detection.get("label") or "").strip()
        class_index = class_indices.get(class_name.casefold())
        bbox = detection.get("bbox")
        if class_index is None or not isinstance(bbox, list) or len(bbox) != 4:
            continue
        try:
            x1, y1, x2, y2 = (float(value) for value in bbox)
        except (TypeError, ValueError):
            continue
        scale = 1.0 if max(abs(x1), abs(y1), abs(x2), abs(y2)) <= 1.0 else 1000.0
        x1, y1, x2, y2 = (max(0.0, min(scale, value)) / scale for value in (x1, y1, x2, y2))
        if x2 <= x1 or y2 <= y1:
            continue
        x_center = (x1 + x2) / 2
        y_center = (y1 + y2) / 2
        labels.append(f"{class_index} {x_center:.6f} {y_center:.6f} {x2 - x1:.6f} {y2 - y1:.6f}")
    return "\n".join(labels)


def _annotate_one(item: dict[str, Any], params: dict[str, Any], classes: list[str], prompt: str) -> dict[str, Any]:
    payload = {
        "model": params["model_name"],
        "messages": [
            {"role": "system", "content": "You return strictly valid JSON for image detection tasks."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": _image_data_url(str(item["local_path"]))}},
                ],
            },
        ],
        "temperature": 0,
    }
    request = Request(
        _chat_completions_url(str(params["base_url"])),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {params['api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        response_payload = json.loads(response.read().decode("utf-8"))
    content = _extract_response_content(response_payload)
    return {
        "batch_item_id": item["batch_item_id"],
        "status": "succeeded",
        "content": {
            "format": "yolo",
            "label_text": _to_yolo_labels(_decode_json_content(content), classes),
        },
    }


def execute_batch(params: dict[str, Any], report: Callable[..., None]) -> dict[str, Any]:
    script_params = params.get("script_params") or {}
    classes = _parse_classes(script_params.get("classes"))
    if not classes:
        raise ValueError("classes is required when the annotation project has no configured classes")
    prompt = _build_prompt(classes, str(script_params.get("prompt") or ""))
    results: list[dict[str, Any]] = []
    items = params.get("items") or []
    for index, item in enumerate(items, start=1):
        try:
            results.append(_annotate_one(item, script_params, classes, prompt))
            message = "vision model annotation completed"
        except (HTTPError, URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
            results.append({
                "batch_item_id": item.get("batch_item_id"),
                "status": "failed",
                "error": f"vision model annotation failed: {exc}",
            })
            message = "vision model annotation failed"
        report(processed=index, total=len(items), message=message)
    return {"items": results}
