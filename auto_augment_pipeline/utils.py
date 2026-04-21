from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from models import ImagePayload


def require_cv2():
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "opencv_python is required for image processing features") from exc
    return cv2


def require_numpy():
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "numpy is required for image processing features") from exc
    return np


def strip_data_url_prefix(data: str) -> str:
    if data.startswith("data:") and "," in data:
        return data.split(",", 1)[1]
    return data


def load_image_bytes(payload: ImagePayload) -> bytes:
    if payload.path:
        return Path(payload.path).expanduser().read_bytes()
    if not payload.base64_data:
        raise ValueError("image payload is empty")
    return base64.b64decode(strip_data_url_prefix(payload.base64_data))


def image_bytes_to_data_url(image_bytes: bytes, mime_type: str = "image/png") -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def payload_to_data_url(payload: ImagePayload) -> str:
    return image_bytes_to_data_url(load_image_bytes(payload), payload.mime_type)


def load_cv2_image(payload: ImagePayload):
    cv2 = require_cv2()
    np = require_numpy()
    image_bytes = load_image_bytes(payload)
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("failed to decode image")
    return image


def image_size(payload: ImagePayload) -> tuple[int, int]:
    image = load_cv2_image(payload)
    height, width = image.shape[:2]
    return width, height


def crop_payload_from_cv2(
    image: Any, x1: int, y1: int, x2: int, y2: int, mime_type: str = "image/png"
) -> ImagePayload:
    cv2 = require_cv2()
    cropped = image[max(0, y1): max(0, y2), max(0, x1): max(0, x2)]
    if cropped.size == 0:
        raise ValueError("crop region is empty")
    ok, encoded = cv2.imencode(".png", cropped)
    if not ok:
        raise ValueError("failed to encode cropped image")
    return ImagePayload(
        base64_data=image_bytes_to_data_url(
            encoded.tobytes(), mime_type=mime_type),
        mime_type=mime_type,
    )


def content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return str(content)


def extract_json_block(text: str) -> dict[str, Any] | list[Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3:
            candidate = "\n".join(lines[1:-1]).strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    for start_char, end_char in (("{", "}"), ("[", "]")):
        start = candidate.find(start_char)
        end = candidate.rfind(end_char)
        if start >= 0 and end > start:
            return json.loads(candidate[start: end + 1])
    raise ValueError("provider response does not contain valid JSON")


def clamp(value: float, lower: int, upper: int) -> int:
    return int(max(lower, min(upper, round(value))))
