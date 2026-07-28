"""A deliberately obvious script used to verify the batch annotation chain."""
from __future__ import annotations

from typing import Any, Callable


definition = {
    "key": "fixed_center_box_demo",
    "version": "1.0.0",
    "description": "Generate one fixed YOLO centre box per image for integration checks.",
}


def execute_batch(params: dict[str, Any], report: Callable[..., None]) -> dict[str, Any]:
    script_params = params.get("script_params") or {}
    class_index = int(script_params.get("class_index", 0))
    box_width = float(script_params.get("box_width", 0.4))
    box_height = float(script_params.get("box_height", 0.4))
    items = params.get("items") or []
    results = []
    for index, item in enumerate(items, start=1):
        results.append(
            {
                "batch_item_id": item["batch_item_id"],
                "status": "succeeded",
                "content": {
                    "format": "yolo",
                    "label_text": f"{class_index} 0.5 0.5 {box_width:.6f} {box_height:.6f}",
                },
            }
        )
        report(processed=index, total=len(items), message="fixed centre box generated")
    return {"items": results}
