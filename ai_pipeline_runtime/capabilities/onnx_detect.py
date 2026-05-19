from __future__ import annotations

import logging
import os
from typing import Any

import requests

from models import AnnotationResult, TaskPayload
from utils import strip_data_url_prefix
from .base import AnnotationNormalizationMixin, Capability, ProviderResolver, capability_metadata

logger = logging.getLogger(__name__)


@capability_metadata(
    display_name="ONNX 检测模型",
    category="model",
    recommended_output_key="detections",
    input_types=["image"],
    output_type="annotations",
    scene_types=["assist_annotation", "general"],
    parameter_fields=[
        {
            "key": "resource_slot",
            "label": "资源槽位",
            "widget": "text",
            "default_value": "detector_model",
            "description": "从绑定层的资源槽位中读取模型资源。",
        },
        {
            "key": "model_id",
            "label": "模型资源",
            "binding_kind": "resource",
            "widget": "resource-select",
            "resource_type": "onnx_model",
            "task_kind": "detection_bbox",
            "deployed_only": True,
            "description": "默认绑定到模板资源槽位，运行时由项目 Binding 选择具体模型。",
        },
        {
            "key": "score_threshold",
            "label": "置信度阈值",
            "value_type": "number",
            "widget": "number",
            "default_value": 0.0,
        },
        {
            "key": "class_match_score",
            "label": "类别匹配阈值",
            "value_type": "number",
            "widget": "number",
            "default_value": 0.72,
        },
        {
            "key": "inference_mode",
            "label": "推理模式",
            "widget": "select",
            "options": [
                {"label": "whole", "value": "whole"},
                {"label": "tile", "value": "tile"},
            ],
        },
        {
            "key": "tile_size",
            "label": "切片尺寸",
            "widget": "text",
        },
        {
            "key": "tile_overlap",
            "label": "切片重叠",
            "value_type": "number",
            "widget": "number",
        },
        {
            "key": "merge_iou",
            "label": "合并 IoU",
            "value_type": "number",
            "widget": "number",
        },
        {
            "key": "return_global_coords",
            "label": "返回全局坐标",
            "value_type": "boolean",
            "widget": "switch",
        },
    ],
)
class OnnxDetectCapability(AnnotationNormalizationMixin, Capability):
    name = "onnx_detect"
    description = "Run a deployed ONNX detection model selected from resource bindings."
    requires_provider = False

    def __init__(self) -> None:
        self._deploy_base_url = (
            os.getenv("MODEL_DEPLOY_URL")
            or os.getenv("MODEL_DEPLOY_BASE_URL")
            or "http://127.0.0.1:8082"
        ).rstrip("/")
        self._timeout_seconds = float(os.getenv("MODEL_DEPLOY_TIMEOUT_SECONDS", "60"))

    def execute(
        self,
        payload: TaskPayload,
        params: dict[str, Any],
        context: ProviderResolver,
        provider_name: str | None = None,
    ) -> AnnotationResult:
        image = payload.primary_image
        if image is None or not image.base64_data:
            raise ValueError("onnx_detect requires a base64 image payload")

        model_id = self._resolve_model_id(params)
        classes = self._require_classes(payload, params)
        backend_payload = self._predict(model_id, image.base64_data, params)
        if not backend_payload.get("success", False):
            raise ValueError(
                backend_payload.get("error") or f"onnx model {model_id} prediction failed"
            )

        raw_results = backend_payload.get("results") or []
        normalized = self._normalize_annotations(
            [
                {
                    "label": item.get("class_name") or item.get("label"),
                    "bbox": item.get("box") or item.get("bbox") or {},
                    "confidence": item.get("confidence"),
                }
                for item in raw_results
                if isinstance(item, dict)
            ],
            width=int(backend_payload.get("image_width", 0) or 0),
            height=int(backend_payload.get("image_height", 0) or 0),
            allowed_classes=classes,
            min_class_match_score=float(params.get("class_match_score", 0.72)),
            max_label_distance_ratio=float(params.get("max_label_distance_ratio", 0.25)),
        )

        score_threshold = float(params.get("score_threshold", 0.0))
        annotations = [
            item
            for item in normalized
            if item.confidence is None or item.confidence >= score_threshold
        ]
        logger.info(
            "onnx_detect model_id=%s raw_count=%s filtered_count=%s",
            model_id,
            len(raw_results),
            len(annotations),
        )
        return AnnotationResult(
            capability=self.name,
            provider=f"model_deploy:{model_id}",
            image_width=int(backend_payload.get("image_width", 0) or 0),
            image_height=int(backend_payload.get("image_height", 0) or 0),
            annotations=annotations,
            summary=f"ONNX detection returned {len(annotations)} annotations.",
            raw={
                "model_id": model_id,
                "task_kind": backend_payload.get("task_kind"),
                "backend": backend_payload.get("backend"),
                "device": backend_payload.get("device"),
                "raw_results": raw_results,
            },
        )

    def _resolve_model_id(self, params: dict[str, Any]) -> int:
        candidate_values = [
            params.get("model_id"),
            self._read_resource_binding_value(params, "model_id"),
            self._read_resource_binding_value(params, "resource_id"),
        ]
        for candidate in candidate_values:
            model_id = self._parse_model_id(candidate)
            if model_id is not None:
                return model_id
        raise ValueError("onnx_detect requires resource binding with model_id")

    def _read_resource_binding_value(
        self,
        params: dict[str, Any],
        field_name: str,
    ) -> Any:
        resource_bindings = params.get("resource_bindings")
        if not isinstance(resource_bindings, dict):
            return None
        preferred_slot = str(params.get("resource_slot") or "detector_model").strip() or "detector_model"
        slot_value = resource_bindings.get(preferred_slot)
        if isinstance(slot_value, dict) and field_name in slot_value:
            return slot_value.get(field_name)
        for value in resource_bindings.values():
            if isinstance(value, dict) and field_name in value:
                return value.get(field_name)
        return None

    def _parse_model_id(self, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, int) and value > 0:
            return value
        text = str(value).strip()
        if not text:
            return None
        if text.startswith("model:"):
            text = text.split(":", 1)[1].strip()
        return int(text) if text.isdigit() and int(text) > 0 else None

    def _predict(
        self,
        model_id: int,
        image_base64: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        inference_params = self._build_inference_params(params)
        response = requests.post(
            f"{self._deploy_base_url}/predict/{model_id}/base64",
            json={
                "image": strip_data_url_prefix(image_base64),
                "inference_params": inference_params or None,
            },
            timeout=(10, self._timeout_seconds),
        )
        try:
            payload = response.json()
        except Exception as exc:
            raise ValueError(f"model_deploy returned invalid JSON: {exc}") from exc
        if response.status_code != 200:
            raise ValueError(payload.get("detail") or payload.get("error") or response.text)
        if not isinstance(payload, dict):
            raise ValueError("model_deploy returned unexpected payload")
        return payload

    def _build_inference_params(self, params: dict[str, Any]) -> dict[str, Any]:
        inference_keys = {
            "input_type",
            "inference_mode",
            "tile_size",
            "tile_overlap",
            "merge_strategy",
            "merge_iou",
            "edge_filter",
            "return_global_coords",
        }
        payload = {
            key: params[key]
            for key in inference_keys
            if key in params and params[key] is not None
        }
        extra = params.get("inference_extra")
        if isinstance(extra, dict) and extra:
            payload["extra"] = extra
        return payload
