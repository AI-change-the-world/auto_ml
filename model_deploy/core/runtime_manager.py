"""
Runtime Manager
管理模型会话的加载、卸载和推理，不再使用子进程。
"""
from __future__ import annotations

import base64
import binascii
import gc
import io
import math
import threading
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
        self.class_names: List[str] = []
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

            with self._lock:
                self.session = session
                self.input_name = input_meta.name
                self.input_shape = list(input_meta.shape)
                self.status = "running"
                self.last_error = None

            logger.info(
                f"Runtime session loaded: model_id={self.model_id}, "
                f"device={self.device}, task_kind={self.task_kind}, providers={providers}"
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
            if self._use_tile_inference(orig_width, orig_height, normalized_params):
                results = self._predict_by_tiles(
                    session=session,
                    input_name=input_name,
                    input_shape=input_shape,
                    image=image,
                    params=normalized_params,
                )
            else:
                results = self._run_single_inference(
                    session=session,
                    input_name=input_name,
                    input_shape=input_shape,
                    image=image,
                )

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
    ) -> List[Dict[str, Any]]:
        orig_width, orig_height = image.size
        input_tensor = self._preprocess(image, input_shape)
        outputs = session.run(None, {input_name: input_tensor})
        return self._postprocess_detections(
            outputs=outputs,
            input_shape=input_shape,
            orig_width=orig_width,
            orig_height=orig_height,
        )

    def _predict_by_tiles(
        self,
        session: Any,
        input_name: str,
        input_shape: List[Any],
        image: Image.Image,
        params: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        orig_width, orig_height = image.size
        tile_size = int(params["tile_size"])
        overlap = float(params["tile_overlap"])
        merge_iou = float(params["merge_iou"])
        edge_filter = bool(params["edge_filter"])

        tile_boxes = self._build_tile_boxes(orig_width, orig_height, tile_size, overlap)
        merged_results: List[Dict[str, Any]] = []

        for left, top, right, bottom in tile_boxes:
            tile = image.crop((left, top, right, bottom))
            tile_width, tile_height = tile.size
            input_tensor = self._preprocess(tile, input_shape)
            outputs = session.run(None, {input_name: input_tensor})
            tile_results = self._postprocess_detections(
                outputs=outputs,
                input_shape=input_shape,
                orig_width=tile_width,
                orig_height=tile_height,
                iou_threshold=merge_iou,
                apply_nms=False,
            )

            for item in tile_results:
                global_item = self._to_global_coords(item, left, top)
                if edge_filter and self._is_edge_detection(global_item, left, top, right, bottom, orig_width, orig_height):
                    continue
                merged_results.append(global_item)

        return self._nms(merged_results, merge_iou)

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

    def _postprocess_detections(
        self,
        outputs: List[np.ndarray],
        input_shape: List[Any],
        orig_width: int,
        orig_height: int,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        apply_nms: bool = True,
    ) -> List[Dict[str, Any]]:
        if not outputs:
            return []

        predictions = outputs[0][0]
        if len(predictions.shape) == 2 and predictions.shape[0] < predictions.shape[1]:
            predictions = predictions.T

        input_height = self._normalize_dim(input_shape[2] if len(input_shape) > 2 else None)
        input_width = self._normalize_dim(input_shape[3] if len(input_shape) > 3 else None)

        detections: List[Dict[str, Any]] = []
        for pred in predictions:
            if len(pred) < 5:
                continue

            x_center, y_center, width, height = pred[0:4]
            confidence = float(pred[4])
            if confidence < conf_threshold:
                continue

            class_scores = pred[5:]
            class_id = 0
            class_conf = 1.0
            if len(class_scores) > 0:
                class_id = int(np.argmax(class_scores))
                class_conf = float(class_scores[class_id])

            x1 = max(0.0, (float(x_center) - float(width) / 2.0) / input_width * orig_width)
            y1 = max(0.0, (float(y_center) - float(height) / 2.0) / input_height * orig_height)
            x2 = min(float(orig_width), (float(x_center) + float(width) / 2.0) / input_width * orig_width)
            y2 = min(float(orig_height), (float(y_center) + float(height) / 2.0) / input_height * orig_height)

            if x2 <= x1 or y2 <= y1:
                continue

            class_name = (
                self.class_names[class_id]
                if class_id < len(self.class_names)
                else f"class_{class_id}"
            )

            detections.append(
                {
                    "type": "obb" if self.task_kind == "detection_obb" else "bbox",
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": confidence * class_conf,
                    "box": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    },
                }
            )

        if not apply_nms:
            return detections
        return self._nms(detections, iou_threshold)

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
                if self._iou(best["box"], item["box"]) < iou_threshold
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

    def _error_response(self, error: str) -> Dict[str, Any]:
        return {
            "success": False,
            "task_kind": self.task_kind,
            "backend": self.backend,
            "device": self.device,
            "error": error,
        }


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
