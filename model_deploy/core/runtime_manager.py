"""
Runtime Manager
管理模型会话的加载、卸载和推理，不再使用子进程。
"""
from __future__ import annotations

import base64
import binascii
import gc
import io
import threading
from typing import Any, Dict, List, Optional

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

    def predict(self, image_data: bytes) -> Dict[str, Any]:
        """使用二进制图像推理"""
        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            return self.predict_image(image)
        except Exception as e:
            logger.error(f"Predict failed: model_id={self.model_id}, error={e}")
            return self._error_response(str(e))

    def predict_base64(self, image_base64: str) -> Dict[str, Any]:
        """使用 base64 图像推理"""
        try:
            encoded = image_base64 or ""
            if "," in encoded:
                encoded = encoded.split(",", 1)[1]
            image_data = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            return self.predict_image(image)
        except (binascii.Error, ValueError) as e:
            logger.error(f"Base64 decode failed: model_id={self.model_id}, error={e}")
            return self._error_response(f"Invalid base64 image payload: {e}")
        except Exception as e:
            logger.error(f"Predict base64 failed: model_id={self.model_id}, error={e}")
            return self._error_response(str(e))

    def predict_image(self, image: Image.Image) -> Dict[str, Any]:
        """执行推理"""
        session, input_name, input_shape = self._session_state()
        if session is None or input_name is None:
            return self._error_response("Model runtime session is not loaded")

        try:
            orig_width, orig_height = image.size
            input_tensor = self._preprocess(image, input_shape)
            outputs = session.run(None, {input_name: input_tensor})
            results = self._postprocess_detections(
                outputs=outputs,
                input_shape=input_shape,
                orig_width=orig_width,
                orig_height=orig_height,
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
