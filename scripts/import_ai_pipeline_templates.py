"""
Import legacy ai_pipeline_runtime sample config templates into ai_pipeline tables.

Usage:
  python scripts/import_ai_pipeline_templates.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AUTOML_SERVER_DIR = ROOT / "automl_server"
if str(AUTOML_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOML_SERVER_DIR))

from app.config.database import AsyncSessionLocal  # noqa: E402
from app.db.models import AiPipelineTemplate, AiPipelineTemplateVersion  # noqa: E402
from sqlalchemy import select  # noqa: E402


CONFIG_PATH = ROOT / "ai_pipeline_runtime" / "sample_config.yaml"


def builtin_onnx_templates() -> dict[str, dict]:
    return {
        "onnx_detection_assist": {
            "name": "onnx_detection_assist",
            "display_name": "ONNX 检测辅助标注",
            "description": "Use a deployed ONNX detection model selected from resource bindings.",
            "pipeline_type": "assist_annotation",
            "enabled": True,
            "supported_annotation_types": [0],
            "supported_shapes": ["bbox"],
            "steps": [
                {
                    "name": "onnx_detect",
                    "capability": "onnx_detect",
                    "input_key": "input",
                    "output_key": "assist_annotations",
                    "params": {
                        "resource_slot": "detector_model",
                        "class_match_score": 0.72,
                        "score_threshold": 0.2,
                    },
                }
            ],
            "resource_slots": [
                {
                    "key": "detector_model",
                    "label": "检测模型",
                    "resource_type": "model",
                    "required": True,
                    "filters": {
                        "model_type": "detection",
                        "is_deployed": True,
                    },
                }
            ],
        }
    }


def build_form_schema(name: str, item: dict) -> dict:
    supported_shapes = item.get("supported_shapes") or []
    supported_annotation_types = item.get("supported_annotation_types") or []
    return {
        "template_key": name,
        "name": item.get("display_name") or name,
        "scene_type": item.get("pipeline_type") or "generic",
        "data_inputs": [
            {
                "key": "primary_image",
                "label": "输入图片",
                "value_type": "image",
                "required": True,
                "widget": "image-asset-picker",
            }
        ],
        "runtime_inputs": [
            {
                "key": "user_prompt",
                "label": "提示词",
                "value_type": "string",
                "required": False,
                "widget": "textarea",
                "default_value": "",
            },
            {
                "key": "target_classes",
                "label": "目标类别",
                "value_type": "string_array",
                "required": False,
                "widget": "multi-select",
            },
        ],
        "resource_slots": item.get("resource_slots") or [],
        "legacy_metadata": {
            "supported_shapes": supported_shapes,
            "supported_annotation_types": supported_annotation_types,
        },
    }


async def main() -> None:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"config file not found: {CONFIG_PATH}")

    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    pipelines = payload.get("pipelines") or {}
    if not isinstance(pipelines, dict):
        raise RuntimeError("invalid pipelines in sample_config.yaml")
    pipelines = {
        **pipelines,
        **builtin_onnx_templates(),
    }
    if not pipelines:
        raise RuntimeError("no pipelines found in sample_config.yaml")

    created_count = 0
    skipped_count = 0

    async with AsyncSessionLocal() as session:
        for template_key, item in pipelines.items():
            if not isinstance(item, dict):
                skipped_count += 1
                continue

            existing = await session.scalar(
                select(AiPipelineTemplate).where(
                    AiPipelineTemplate.template_key == template_key,
                    AiPipelineTemplate.is_deleted == False,
                )
            )
            if existing:
                print(f"[skip] template already exists: {template_key}")
                skipped_count += 1
                continue

            scene_type = str(item.get("pipeline_type") or "generic")
            template = AiPipelineTemplate(
                template_key=template_key,
                name=str(item.get("display_name") or template_key),
                description=item.get("description"),
                scene_type=scene_type,
                input_kind="image",
                output_kind="annotation_bbox" if scene_type == "assist_annotation" else "generic",
                status="published" if item.get("enabled", True) else "disabled",
                latest_version=1,
                published_version=1 if item.get("enabled", True) else None,
                is_builtin=True,
                created_by="migration_script",
            )
            session.add(template)
            await session.flush()

            definition_json = dict(item)
            form_schema_json = build_form_schema(template_key, item)
            version = AiPipelineTemplateVersion(
                template_id=template.id,
                version=1,
                definition_json=json.dumps(definition_json, ensure_ascii=False),
                form_schema_json=json.dumps(form_schema_json, ensure_ascii=False),
                change_note="imported from ai_pipeline_runtime/sample_config.yaml",
                is_published=bool(item.get("enabled", True)),
                created_by="migration_script",
            )
            session.add(version)
            created_count += 1
            print(f"[ok] imported template: {template_key}")

        await session.commit()

    print(
        f"ai_pipeline template import completed. created={created_count}, skipped={skipped_count}"
    )


if __name__ == "__main__":
    import asyncio

    if not os.getenv("USE_NACOS"):
        os.environ["USE_NACOS"] = "false"
    asyncio.run(main())
