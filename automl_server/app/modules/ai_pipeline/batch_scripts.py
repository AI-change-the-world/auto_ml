"""Platform-maintained batch script catalog.

The sandbox only accepts keys from this catalog. Adding a production script is a
code deployment: add its metadata here and its implementation under
``ai_pipeline_sandbox/scripts`` with the same key.
"""
from __future__ import annotations

from typing import Any


BUILTIN_BATCH_SCRIPTS: list[dict[str, Any]] = [
    {
        "key": "fixed_center_box_demo",
        "version": "1.0.0",
        "name": "验证脚本：固定中心框",
        "description": "为每个图片样本生成一个固定中心框，仅用于验证批量任务链路。",
        "supported_data_types": [0],
        "supported_annotation_types": [0],
        "parameter_fields": [
            {
                "key": "class_index",
                "label": "类别索引",
                "value_type": "number",
                "required": True,
                "default_value": 0,
                "description": "YOLO 类别索引，从 0 开始。",
                "widget": "number",
            },
            {
                "key": "box_width",
                "label": "框宽度比例",
                "value_type": "number",
                "required": False,
                "default_value": 0.4,
                "widget": "number",
            },
            {
                "key": "box_height",
                "label": "框高度比例",
                "value_type": "number",
                "required": False,
                "default_value": 0.4,
                "widget": "number",
            },
        ],
    },
]


def list_batch_scripts() -> list[dict[str, Any]]:
    return BUILTIN_BATCH_SCRIPTS


def get_batch_script(script_key: str) -> dict[str, Any] | None:
    normalized = (script_key or "").strip()
    return next((item for item in BUILTIN_BATCH_SCRIPTS if item["key"] == normalized), None)
