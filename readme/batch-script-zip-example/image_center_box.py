"""Integration-check script for uploaded batch annotation ZIP packages."""
from __future__ import annotations

from typing import Any, Callable

from PIL import Image

from box_utils import build_center_box, parse_ratio


def execute_batch(params: dict[str, Any], report: Callable[..., None]) -> dict[str, Any]:
    script_params = params.get("script_params") or {}
    class_index = int(script_params.get("class_index", 0))
    box_width = parse_ratio(script_params.get("box_width", 0.5), "box_width")
    box_height = parse_ratio(script_params.get("box_height", 0.5), "box_height")
    items = params.get("items") or []
    results = []

    for index, item in enumerate(items, start=1):
        batch_item_id = item["batch_item_id"]
        try:
            with Image.open(item["local_path"]) as image:
                width, height = image.size
            label_text = build_center_box(class_index, box_width, box_height)
            results.append(
                {
                    "batch_item_id": batch_item_id,
                    "status": "succeeded",
                    "content": {
                        "format": "yolo",
                        "label_text": label_text,
                        "image_width": width,
                        "image_height": height,
                    },
                }
            )
            message = f"generated centre box for {width}x{height} image"
        except Exception as exc:
            results.append(
                {
                    "batch_item_id": batch_item_id,
                    "status": "failed",
                    "error": f"unable to generate centre box: {exc}",
                    "error_detail": {
                        "source": "uploaded_script",
                        "stage": "read_image",
                        "exception_type": exc.__class__.__name__,
                        "message": str(exc),
                    },
                }
            )
            message = "failed to read image"

        report(
            processed=index,
            total=len(items),
            batch_item_id=batch_item_id,
            message=message,
        )

    return {"items": results}
