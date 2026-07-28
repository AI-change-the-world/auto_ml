"""Platform-maintained batch script catalog.

The sandbox only accepts keys from this catalog. Adding a production script is a
code deployment: add its metadata here and its implementation under
``ai_pipeline_sandbox/scripts`` with the same key.
"""
from __future__ import annotations

from typing import Any


BUILTIN_BATCH_SCRIPTS: list[dict[str, Any]] = [
    {
        "key": "vision_llm_bbox_assistant",
        "version": "1.0.0",
        "name": "视觉大模型辅助标注",
        "description": "调用 OpenAI 兼容视觉模型，为图像检测项目生成 YOLO 边界框草稿。",
        "supported_data_types": [0],
        "supported_annotation_types": [0],
        "parameter_fields": [
            {
                "key": "base_url",
                "label": "Base URL",
                "value_type": "string",
                "required": True,
                "description": "OpenAI 兼容服务地址，例如 https://api.openai.com/v1。",
            },
            {
                "key": "model_name",
                "label": "模型名称",
                "value_type": "string",
                "required": True,
                "description": "视觉模型名称。",
            },
            {
                "key": "api_key",
                "label": "API Key",
                "value_type": "secret",
                "required": True,
                "description": "仅在本次 sandbox 执行时解密。",
            },
            {
                "key": "classes",
                "label": "类别",
                "value_type": "string",
                "widget": "textarea",
                "value_source": "annotation_classes",
                "required": True,
                "description": "优先使用所选标注项目的类别；没有类别时请输入逗号或换行分隔的类别名。",
            },
            {
                "key": "prompt",
                "label": "补充提示词",
                "value_type": "string",
                "widget": "textarea",
                "required": False,
                "description": "可选。留空时使用内置 bbox 输出提示词。",
            },
        ],
    },
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
