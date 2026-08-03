"""
Runtime Manager
管理模型会话的加载、卸载和推理，不再使用子进程。
"""
from __future__ import annotations

import base64
import binascii
import gc
import hashlib
import io
import os
import math
import threading
import time
from urllib.request import urlopen
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

from utils.logger import logger
from utils.runtime_env import ensure_runtime_dependencies


class RuntimeInstance:
    """内存中的模型运行时实例"""

    def __init__(
        self,
        model_id: int,
        model_path: str,
        port: Optional[int] = None,
        device: str = "cpu",
        task_kind: str = "detection_bbox",
        backend: str = "onnxruntime",
        class_names: Optional[List[str]] = None,
    ):
        self.model_id = model_id
        self.model_path = model_path
        self.port = port
        self.device = device
        self.task_kind = task_kind
        self.backend = backend
        self.pid: Optional[int] = None
        self.status = "stopped"
        self.last_error: Optional[str] = None
        self.session: Any = None
        self.input_name: Optional[str] = None
        self.input_shape: Optional[List[Any]] = None
        self.class_names: List[str] = list(class_names or [])
        self._lock = threading.RLock()

    def start(self) -> bool:
        """加载模型到内存"""
        try:
            ensure_runtime_dependencies()
            import onnxruntime as ort

            requested_device = (self.device or "cpu").strip().lower()
            available_providers = ort.get_available_providers()
            if requested_device.startswith("cuda"):
                if "CUDAExecutionProvider" not in available_providers:
                    raise RuntimeError(
                        "CUDAExecutionProvider is not available in the current onnxruntime build"
                    )
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            else:
                providers = ["CPUExecutionProvider"]

            self.status = "starting"
            session = ort.InferenceSession(self.model_path, providers=providers)
            input_meta = session.get_inputs()[0]
            self._validate_classification_output_signature(session.get_outputs()[0].shape)

            with self._lock:
                self.session = session
                self.input_name = input_meta.name
                self.input_shape = list(input_meta.shape)
                self.status = "running"
                self.last_error = None

            logger.info(
                f"Runtime session loaded: model_id={self.model_id}, "
                f"device={self.device}, task_kind={self.task_kind}, providers={providers}, "
                f"input_name={self.input_name}, input_shape={self.input_shape}, "
                f"class_count={len(self.class_names)}, "
                f"class_names={self.class_names}, "
                f"model_path={self.model_path}, "
                f"file_size_bytes={self._file_size_bytes(self.model_path)}, "
                f"sha256={self._file_sha256(self.model_path)}"
            )
            return True

        except Exception as e:
            with self._lock:
                self.session = None
                self.input_name = None
                self.input_shape = None
                self.status = "error"
                self.last_error = str(e)
            logger.error(f"Failed to load runtime session: model_id={self.model_id}, error={e}")
            return False

    def stop(self) -> bool:
        """卸载模型会话"""
        try:
            with self._lock:
                session = self.session
                self.session = None
                self.input_name = None
                self.input_shape = None
                self.status = "stopped"
                self.last_error = None

            if session is not None:
                del session
                gc.collect()

            logger.info(f"Runtime session released: model_id={self.model_id}")
            return True
        except Exception as e:
            with self._lock:
                self.status = "error"
                self.last_error = str(e)
            logger.error(f"Failed to release runtime session: model_id={self.model_id}, error={e}")
            return False

    def health_check(self) -> bool:
        """健康检查"""
        with self._lock:
            return self.session is not None and self.status == "running"

    def is_running(self) -> bool:
        """检查会话是否已加载"""
        return self.health_check()

    def predict(
        self,
        image_data: bytes,
        inference_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """使用二进制图像推理"""
        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            return self.predict_image(image, inference_params=inference_params)
        except Exception as e:
            logger.error(f"Predict failed: model_id={self.model_id}, error={e}")
            return self._error_response(str(e))

    def predict_base64(
        self,
        image_base64: str,
        inference_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """使用 base64 图像推理"""
        try:
            encoded = image_base64 or ""
            if "," in encoded:
                encoded = encoded.split(",", 1)[1]
            image_data = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            return self.predict_image(image, inference_params=inference_params)
        except (binascii.Error, ValueError) as e:
            logger.error(f"Base64 decode failed: model_id={self.model_id}, error={e}")
            return self._error_response(f"Invalid base64 image payload: {e}")
        except Exception as e:
            logger.error(f"Predict base64 failed: model_id={self.model_id}, error={e}")
            return self._error_response(str(e))

    def predict_url(
        self,
        image_url: str,
        inference_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """使用 URL 图像推理"""
        try:
            with urlopen(image_url) as response:
                image_data = response.read()
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            return self.predict_image(image, inference_params=inference_params)
        except Exception as e:
            logger.error(f"Predict url failed: model_id={self.model_id}, error={e}")
            return self._error_response(str(e))

    def predict_image(
        self,
        image: Image.Image,
        inference_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行推理"""
        session, input_name, input_shape = self._session_state()
        if session is None or input_name is None:
            return self._error_response("Model runtime session is not loaded")

        try:
            orig_width, orig_height = image.size
            normalized_params = self._normalize_inference_params(inference_params, input_shape)
            trace_id = f"{self.model_id}-{time.time_ns()}"
            logger.info(
                f"[predict] start trace_id={trace_id}, model_id={self.model_id}, "
                f"task_kind={self.task_kind}, backend={self.backend}, device={self.device}, "
                f"image={orig_width}x{orig_height}, input_shape={input_shape}, params={normalized_params}"
            )
            if self._use_tile_inference(orig_width, orig_height, normalized_params):
                results, debug_summary = self._predict_by_tiles(
                    session=session,
                    input_name=input_name,
                    input_shape=input_shape,
                    image=image,
                    params=normalized_params,
                )
            else:
                results, debug_summary = self._run_single_inference(
                    session=session,
                    input_name=input_name,
                    input_shape=input_shape,
                    image=image,
                )

            result_summary = self._summarize_results(results)
            log_message = (
                f"[predict] done trace_id={trace_id}, model_id={self.model_id}, "
                f"result_count={len(results)}, result_summary={result_summary}, debug={debug_summary}"
            )
            if results:
                logger.info(log_message)
            else:
                logger.warning(log_message)

            return {
                "success": True,
                "task_kind": self.task_kind,
                "backend": self.backend,
                "device": self.device,
                "results": results,
                "image_width": orig_width,
                "image_height": orig_height,
            }
        except Exception as e:
            logger.error(f"Inference failed: model_id={self.model_id}, error={e}")
            with self._lock:
                self.last_error = str(e)
            return self._error_response(str(e))

    def _run_single_inference(
        self,
        session: Any,
        input_name: str,
        input_shape: List[Any],
        image: Image.Image,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        orig_width, orig_height = image.size
        input_tensor = self._preprocess(image, input_shape)
        outputs = session.run(None, {input_name: input_tensor})
        results, postprocess_summary = self._postprocess_outputs(
            outputs=outputs,
            input_shape=input_shape,
            orig_width=orig_width,
            orig_height=orig_height,
        )
        return results, {
            "mode": "direct",
            "input_tensor": self._summarize_array(input_tensor),
            "outputs": self._summarize_outputs(outputs),
            "postprocess": postprocess_summary,
        }

    def _predict_by_tiles(
        self,
        session: Any,
        input_name: str,
        input_shape: List[Any],
        image: Image.Image,
        params: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        orig_width, orig_height = image.size
        tile_size = int(params["tile_size"])
        overlap = float(params["tile_overlap"])
        merge_iou = float(params["merge_iou"])
        edge_filter = bool(params["edge_filter"])

        tile_boxes = self._build_tile_boxes(orig_width, orig_height, tile_size, overlap)
        merged_results: List[Dict[str, Any]] = []
        filtered_edge_count = 0
        tiles_with_candidates = 0
        sample_tile_summary: Optional[Dict[str, Any]] = None

        for left, top, right, bottom in tile_boxes:
            tile = image.crop((left, top, right, bottom))
            tile_width, tile_height = tile.size
            input_tensor = self._preprocess(tile, input_shape)
            outputs = session.run(None, {input_name: input_tensor})
            tile_results, tile_postprocess_summary = self._postprocess_outputs(
                outputs=outputs,
                input_shape=input_shape,
                orig_width=tile_width,
                orig_height=tile_height,
                iou_threshold=merge_iou,
                apply_nms=False,
            )
            if tile_results:
                tiles_with_candidates += 1
            if sample_tile_summary is None:
                sample_tile_summary = {
                    "tile_box": [left, top, right, bottom],
                    "input_tensor": self._summarize_array(input_tensor),
                    "outputs": self._summarize_outputs(outputs),
                    "postprocess": tile_postprocess_summary,
                }

            for item in tile_results:
                global_item = self._to_global_coords(item, left, top)
                if edge_filter and self._is_edge_detection(global_item, left, top, right, bottom, orig_width, orig_height):
                    filtered_edge_count += 1
                    continue
                merged_results.append(global_item)

        final_results = self._nms(merged_results, merge_iou)
        return final_results, {
            "mode": "tile",
            "tile_count": len(tile_boxes),
            "tile_size": tile_size,
            "tile_overlap": overlap,
            "merge_iou": merge_iou,
            "edge_filter": edge_filter,
            "tiles_with_candidates": tiles_with_candidates,
            "filtered_edge_count": filtered_edge_count,
            "merged_before_nms": len(merged_results),
            "merged_after_nms": len(final_results),
            "sample_tile": sample_tile_summary,
        }

    def _postprocess_outputs(
        self,
        outputs: List[np.ndarray],
        input_shape: List[Any],
        orig_width: int,
        orig_height: int,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        apply_nms: bool = True,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if self.task_kind == "classification":
            return self._postprocess_classification(outputs, conf_threshold=conf_threshold)
        return self._postprocess_detections(
            outputs=outputs,
            input_shape=input_shape,
            orig_width=orig_width,
            orig_height=orig_height,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            apply_nms=apply_nms,
        )

    def _session_state(self) -> tuple[Any, Optional[str], List[Any]]:
        with self._lock:
            session = self.session
            input_name = self.input_name
            input_shape = list(self.input_shape or [])
        return session, input_name, input_shape

    def _preprocess(self, image: Image.Image, input_shape: List[Any]) -> np.ndarray:
        input_height = self._normalize_dim(input_shape[2] if len(input_shape) > 2 else None)
        input_width = self._normalize_dim(input_shape[3] if len(input_shape) > 3 else None)

        image = image.resize((input_width, input_height))
        img_array = np.array(image).astype(np.float32) / 255.0
        if len(img_array.shape) == 3:
            img_array = np.transpose(img_array, (2, 0, 1))
        img_array = np.expand_dims(img_array, axis=0)
        return img_array

    def _validate_classification_output_signature(self, output_shape: List[Any]) -> None:
        """Reject a detection ONNX before it can be misreported as classification."""
        if self.task_kind != "classification":
            return
        if len(output_shape) != 2:
            raise RuntimeError(
                "Classification deployment requires an ONNX output shaped "
                f"[batch, classes], but received {output_shape}. "
                "The cached artifact does not match this model; redeploy after refreshing model_deploy."
            )
        class_count = output_shape[1]
        if (
            self.class_names
            and isinstance(class_count, int)
            and class_count != len(self.class_names)
        ):
            raise RuntimeError(
                "Classification ONNX output class count does not match the registered class names: "
                f"output={class_count}, registered={len(self.class_names)}. "
                "The cached artifact does not match this model; redeploy after refreshing model_deploy."
            )

    def _postprocess_detections(
        self,
        outputs: List[np.ndarray],
        input_shape: List[Any],
        orig_width: int,
        orig_height: int,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        apply_nms: bool = True,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not outputs:
            return [], {
                "conf_threshold": conf_threshold,
                "iou_threshold": iou_threshold,
                "apply_nms": apply_nms,
                "raw_prediction_count": 0,
                "skipped_short": 0,
                "skipped_below_conf": 0,
                "skipped_invalid_box": 0,
                "candidates_before_nms": 0,
                "candidates_after_nms": 0,
                "top_raw_candidates": [],
            }

        predictions = outputs[0][0]
        transposed = False
        if len(predictions.shape) == 2 and predictions.shape[0] < predictions.shape[1]:
            predictions = predictions.T
            transposed = True

        input_height = self._normalize_dim(input_shape[2] if len(input_shape) > 2 else None)
        input_width = self._normalize_dim(input_shape[3] if len(input_shape) > 3 else None)

        detections: List[Dict[str, Any]] = []
        skipped_short = 0
        skipped_below_conf = 0
        skipped_invalid_box = 0
        top_raw_candidates: List[Dict[str, Any]] = []
        for pred in predictions:
            if len(pred) < 5:
                skipped_short += 1
                continue

            x_center, y_center, width, height = pred[0:4]
            class_id, confidence = self._parse_detection_class(pred)
            class_name = (
                self.class_names[class_id]
                if class_id < len(self.class_names)
                else f"class_{class_id}"
            )
            self._append_top_candidate(top_raw_candidates, {
                "class_id": class_id,
                "class_name": class_name,
                "confidence": self._round_float(confidence),
            })
            if confidence < conf_threshold:
                skipped_below_conf += 1
                continue

            x1 = max(0.0, (float(x_center) - float(width) / 2.0) / input_width * orig_width)
            y1 = max(0.0, (float(y_center) - float(height) / 2.0) / input_height * orig_height)
            x2 = min(float(orig_width), (float(x_center) + float(width) / 2.0) / input_width * orig_width)
            y2 = min(float(orig_height), (float(y_center) + float(height) / 2.0) / input_height * orig_height)

            if x2 <= x1 or y2 <= y1:
                skipped_invalid_box += 1
                continue

            detections.append(
                {
                    "type": "obb" if self.task_kind == "detection_obb" else "bbox",
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": confidence,
                    "box": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    },
                }
            )

        if not apply_nms:
            return detections, {
                "conf_threshold": conf_threshold,
                "iou_threshold": iou_threshold,
                "apply_nms": apply_nms,
                "transposed": transposed,
                "raw_prediction_count": int(predictions.shape[0]) if predictions.ndim > 0 else 0,
                "input_resize": {"width": input_width, "height": input_height},
                "skipped_short": skipped_short,
                "skipped_below_conf": skipped_below_conf,
                "skipped_invalid_box": skipped_invalid_box,
                "candidates_before_nms": len(detections),
                "candidates_after_nms": len(detections),
                "top_raw_candidates": top_raw_candidates,
            }
        final_detections = self._nms(detections, iou_threshold)
        return final_detections, {
            "conf_threshold": conf_threshold,
            "iou_threshold": iou_threshold,
            "apply_nms": apply_nms,
            "transposed": transposed,
            "raw_prediction_count": int(predictions.shape[0]) if predictions.ndim > 0 else 0,
            "input_resize": {"width": input_width, "height": input_height},
            "skipped_short": skipped_short,
            "skipped_below_conf": skipped_below_conf,
            "skipped_invalid_box": skipped_invalid_box,
            "candidates_before_nms": len(detections),
            "candidates_after_nms": len(final_detections),
            "top_raw_candidates": top_raw_candidates,
        }

    def _parse_detection_class(self, pred: np.ndarray) -> tuple[int, float]:
        class_count = len(self.class_names)

        # Ultralytics 导出的检测 ONNX 常见格式为:
        # [x, y, w, h, cls0, cls1, ...]，没有单独 objectness。
        if class_count > 0 and len(pred) == class_count + 4:
            class_scores = pred[4:4 + class_count]
            class_id = int(np.argmax(class_scores))
            confidence = float(class_scores[class_id])
            return class_id, confidence

        # 兼容包含 objectness 的旧式输出:
        # [x, y, w, h, obj, cls0, cls1, ...]
        if class_count > 0 and len(pred) >= class_count + 5:
            objectness = float(pred[4])
            class_scores = pred[5:5 + class_count]
            class_id = int(np.argmax(class_scores))
            confidence = objectness * float(class_scores[class_id])
            return class_id, confidence

        # 无法从元信息判断时的兜底逻辑，优先按 Ultralytics 当前导出格式处理。
        class_scores = pred[4:]
        if len(class_scores) == 0:
            return 0, 0.0
        class_id = int(np.argmax(class_scores))
        confidence = float(class_scores[class_id])
        return class_id, confidence

    def _postprocess_classification(
        self,
        outputs: List[np.ndarray],
        conf_threshold: float = 0.25,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not outputs:
            return [], {
                "conf_threshold": conf_threshold,
                "prediction_count": 0,
                "accepted": False,
                "top_scores": [],
            }

        predictions = np.asarray(outputs[0])
        if predictions.size == 0:
            return [], {
                "conf_threshold": conf_threshold,
                "prediction_count": 0,
                "accepted": False,
                "top_scores": [],
            }

        if predictions.ndim == 0:
            predictions = predictions.reshape(1)
        if predictions.ndim > 1:
            predictions = predictions[0]

        predictions = predictions.astype(np.float32).reshape(-1)
        if predictions.size == 0:
            return [], {
                "conf_threshold": conf_threshold,
                "prediction_count": 0,
                "accepted": False,
                "top_scores": [],
            }
        if self.class_names and predictions.size != len(self.class_names):
            raise RuntimeError(
                "Classification output class count does not match the registered class names: "
                f"output={predictions.size}, registered={len(self.class_names)}"
            )

        class_id = int(np.argmax(predictions))
        confidence = float(predictions[class_id])
        top_scores = self._top_classification_scores(predictions)
        if confidence < conf_threshold:
            return [], {
                "conf_threshold": conf_threshold,
                "prediction_count": int(predictions.size),
                "accepted": False,
                "top_scores": top_scores,
            }

        class_name = (
            self.class_names[class_id]
            if 0 <= class_id < len(self.class_names)
            else f"class_{class_id}"
        )
        return [
            {
                "type": "classification",
                "class_id": class_id,
                "class_name": class_name,
                "confidence": confidence,
            }
        ], {
            "conf_threshold": conf_threshold,
            "prediction_count": int(predictions.size),
            "accepted": True,
            "top_scores": top_scores,
        }

    def _nms(self, detections: List[Dict[str, Any]], iou_threshold: float) -> List[Dict[str, Any]]:
        if not detections:
            return []

        ordered = sorted(detections, key=lambda item: item["confidence"], reverse=True)
        kept: List[Dict[str, Any]] = []
        while ordered:
            best = ordered.pop(0)
            kept.append(best)
            ordered = [
                item for item in ordered
                if item.get("class_id") != best.get("class_id")
                or self._iou(best["box"], item["box"]) < iou_threshold
            ]
        return kept

    def _iou(self, box1: Dict[str, float], box2: Dict[str, float]) -> float:
        x1 = max(box1["x1"], box2["x1"])
        y1 = max(box1["y1"], box2["y1"])
        x2 = min(box1["x2"], box2["x2"])
        y2 = min(box1["y2"], box2["y2"])

        intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        area1 = max(0.0, box1["x2"] - box1["x1"]) * max(0.0, box1["y2"] - box1["y1"])
        area2 = max(0.0, box2["x2"] - box2["x1"]) * max(0.0, box2["y2"] - box2["y1"])
        union = area1 + area2 - intersection
        if union <= 0:
            return 0.0
        return intersection / union

    def _normalize_inference_params(
        self,
        inference_params: Optional[Dict[str, Any]],
        input_shape: List[Any],
    ) -> Dict[str, Any]:
        payload = dict(inference_params or {})
        default_tile = max(
            self._normalize_dim(input_shape[2] if len(input_shape) > 2 else None),
            self._normalize_dim(input_shape[3] if len(input_shape) > 3 else None),
        )
        return {
            "inference_mode": str(payload.get("inference_mode") or "direct").strip().lower(),
            "tile_size": self._normalize_dim(payload.get("tile_size"), default=default_tile),
            "tile_overlap": self._normalize_ratio(payload.get("tile_overlap"), default=0.2),
            "merge_iou": self._normalize_ratio(payload.get("merge_iou"), default=0.45, allow_one=True),
            "edge_filter": bool(payload.get("edge_filter", False)),
        }

    def _use_tile_inference(
        self,
        image_width: int,
        image_height: int,
        params: Dict[str, Any],
    ) -> bool:
        if self.task_kind == "classification":
            return False
        if params["inference_mode"] == "tile":
            return True
        if params["inference_mode"] == "direct":
            return False
        tile_size = int(params["tile_size"])
        return image_width > tile_size or image_height > tile_size

    def _build_tile_boxes(
        self,
        image_width: int,
        image_height: int,
        tile_size: int,
        tile_overlap: float,
    ) -> List[Tuple[int, int, int, int]]:
        stride = max(1, int(round(tile_size * (1 - tile_overlap))))
        x_positions = self._axis_positions(image_width, tile_size, stride)
        y_positions = self._axis_positions(image_height, tile_size, stride)
        boxes: List[Tuple[int, int, int, int]] = []
        for top in y_positions:
            for left in x_positions:
                right = min(left + tile_size, image_width)
                bottom = min(top + tile_size, image_height)
                boxes.append((left, top, right, bottom))
        return boxes

    def _axis_positions(self, length: int, tile_size: int, stride: int) -> List[int]:
        if length <= tile_size:
            return [0]

        positions: List[int] = []
        current = 0
        last_start = max(0, length - tile_size)
        while current < last_start:
            positions.append(current)
            current += stride
        if not positions or positions[-1] != last_start:
            positions.append(last_start)
        return positions

    def _to_global_coords(self, item: Dict[str, Any], offset_x: int, offset_y: int) -> Dict[str, Any]:
        updated = dict(item)
        if item.get("box"):
            box = dict(item["box"])
            box["x1"] += offset_x
            box["x2"] += offset_x
            box["y1"] += offset_y
            box["y2"] += offset_y
            updated["box"] = box
        if item.get("points"):
            updated["points"] = [
                {"x": point["x"] + offset_x, "y": point["y"] + offset_y}
                for point in item["points"]
            ]
        if item.get("obb"):
            obb = dict(item["obb"])
            obb["cx"] += offset_x
            obb["cy"] += offset_y
            updated["obb"] = obb
        return updated

    def _is_edge_detection(
        self,
        item: Dict[str, Any],
        left: int,
        top: int,
        right: int,
        bottom: int,
        image_width: int,
        image_height: int,
    ) -> bool:
        box = item.get("box")
        if not isinstance(box, dict):
            return False

        margin = 2.0
        touches_tile_edge = (
            abs(float(box["x1"]) - left) <= margin
            or abs(float(box["y1"]) - top) <= margin
            or abs(float(box["x2"]) - right) <= margin
            or abs(float(box["y2"]) - bottom) <= margin
        )
        touches_image_edge = (
            left <= 0 and abs(float(box["x1"]) - left) <= margin
            or top <= 0 and abs(float(box["y1"]) - top) <= margin
            or right >= image_width and abs(float(box["x2"]) - right) <= margin
            or bottom >= image_height and abs(float(box["y2"]) - bottom) <= margin
        )
        return touches_tile_edge and not touches_image_edge

    def _normalize_ratio(
        self,
        value: Any,
        default: float,
        allow_one: bool = False,
    ) -> float:
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            return default
        upper = 1.0 if allow_one else math.nextafter(1.0, 0.0)
        if normalized < 0:
            return default
        if normalized > upper:
            return upper
        return normalized

    def _normalize_dim(self, value: Any, default: int = 640) -> int:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            return default
        return normalized if normalized > 0 else default

    def _summarize_array(self, array: np.ndarray) -> Dict[str, Any]:
        values = np.asarray(array)
        summary: Dict[str, Any] = {
            "shape": list(values.shape),
            "dtype": str(values.dtype),
            "size": int(values.size),
        }
        if values.size > 0:
            summary.update({
                "min": self._round_float(np.min(values)),
                "max": self._round_float(np.max(values)),
                "mean": self._round_float(np.mean(values)),
            })
        return summary

    def _summarize_outputs(self, outputs: List[np.ndarray]) -> List[Dict[str, Any]]:
        return [self._summarize_array(output) for output in outputs]

    def _summarize_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not results:
            return {"count": 0, "top_results": []}

        ordered = sorted(
            results,
            key=lambda item: float(item.get("confidence", 0.0)),
            reverse=True,
        )
        top_results = [
            {
                "type": item.get("type"),
                "class_id": item.get("class_id"),
                "class_name": item.get("class_name"),
                "confidence": self._round_float(item.get("confidence", 0.0)),
            }
            for item in ordered[:3]
        ]
        return {
            "count": len(results),
            "top_results": top_results,
        }

    def _append_top_candidate(
        self,
        candidates: List[Dict[str, Any]],
        candidate: Dict[str, Any],
        limit: int = 5,
    ) -> None:
        candidates.append(candidate)
        candidates.sort(key=lambda item: float(item.get("confidence", 0.0)), reverse=True)
        del candidates[limit:]

    def _top_classification_scores(self, predictions: np.ndarray, limit: int = 5) -> List[Dict[str, Any]]:
        if predictions.size == 0:
            return []
        limit = max(1, min(limit, int(predictions.size)))
        indices = np.argsort(predictions)[::-1][:limit]
        results: List[Dict[str, Any]] = []
        for class_id in indices:
            idx = int(class_id)
            class_name = (
                self.class_names[idx]
                if 0 <= idx < len(self.class_names)
                else f"class_{idx}"
            )
            results.append({
                "class_id": idx,
                "class_name": class_name,
                "confidence": self._round_float(predictions[idx]),
            })
        return results

    def _round_float(self, value: Any, digits: int = 6) -> float:
        return round(float(value), digits)

    def _error_response(self, error: str) -> Dict[str, Any]:
        return {
            "success": False,
            "task_kind": self.task_kind,
            "backend": self.backend,
            "device": self.device,
            "error": error,
        }

    def _file_sha256(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _file_size_bytes(self, file_path: str) -> int:
        return int(os.path.getsize(file_path))


class RuntimeManager:
    """运行时管理器"""

    def __init__(self):
        self.instances: Dict[int, RuntimeInstance] = {}
        self.last_error: Optional[str] = None
        self._lock = threading.RLock()

    def deploy_model(
        self,
        model_id: int,
        model_path: str,
        device: str = "cpu",
        task_kind: str = "detection_bbox",
        backend: str = "onnxruntime",
        class_names: Optional[List[str]] = None,
    ) -> Optional[RuntimeInstance]:
        """加载模型会话"""
        with self._lock:
            existing = self.instances.get(model_id)
            if existing and existing.is_running():
                self.last_error = None
                logger.info(f"Model {model_id} already deployed in memory")
                return existing
            if existing:
                existing.stop()
                del self.instances[model_id]

        instance = RuntimeInstance(
            model_id=model_id,
            model_path=model_path,
            port=None,
            device=device,
            task_kind=task_kind,
            backend=backend,
            class_names=class_names,
        )
        if instance.start():
            with self._lock:
                self.instances[model_id] = instance
                self.last_error = None
            return instance

        self.last_error = instance.last_error or "Failed to load runtime session"
        return None

    def undeploy_model(self, model_id: int) -> bool:
        """卸载模型会话"""
        with self._lock:
            instance = self.instances.pop(model_id, None)

        if instance is None:
            logger.info(f"Model {model_id} runtime session already absent")
            return True

        success = instance.stop()
        if not success:
            self.last_error = instance.last_error or "Failed to release runtime session"
        return success

    def get_instance(self, model_id: int) -> Optional[RuntimeInstance]:
        with self._lock:
            return self.instances.get(model_id)

    def get_all_instances(self) -> Dict[int, RuntimeInstance]:
        with self._lock:
            return self.instances.copy()

    def health_check_all(self) -> Dict[int, bool]:
        results: Dict[int, bool] = {}
        for model_id, instance in self.get_all_instances().items():
            is_healthy = instance.health_check()
            results[model_id] = is_healthy
            if not is_healthy:
                logger.warning(f"Instance for model {model_id} is unhealthy")
        return results

    def restart_instance(self, model_id: int) -> bool:
        instance = self.get_instance(model_id)
        if instance is None:
            logger.warning(f"Model {model_id} not deployed")
            return False

        model_path = instance.model_path
        device = instance.device
        task_kind = instance.task_kind
        backend = instance.backend

        self.undeploy_model(model_id)
        return self.deploy_model(model_id, model_path, device, task_kind, backend) is not None


runtime_manager = RuntimeManager()
