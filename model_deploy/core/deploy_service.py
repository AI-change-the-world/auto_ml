"""
部署服务核心逻辑
使用 RabbitMQ 发送状态更新，不直接写数据库
"""
import hashlib
import os
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional

from core.runtime_manager import RuntimeInstance, runtime_manager
from utils.config import download_from_s3, get_deploy_config, get_s3_config
from utils.logger import logger
from utils.mq import publish_model_deployed, publish_model_undeployed

SERVICE_NAME = "model-deploy"


# 内存中维护部署状态（实际状态由主服务管理）
_deployments: Dict[int, Dict[str, Any]] = {}
_deployment_counter = 0


class DeployService:
    """部署服务"""

    @property
    def config(self):
        return get_deploy_config()

    @property
    def s3_config(self):
        return get_s3_config()

    def deploy(
        self,
        model_id: int,
        model_path: str,  # S3 路径
        device: str = "cpu",
        version: str = "v1",
        model_format: str = "onnx",
        task_kind: str = "detection_bbox",
        backend: str = "onnxruntime",
        class_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        部署模型

        Args:
            model_id: 模型ID（业务ID，由主服务提供）
            model_path: S3 上的模型路径
            device: 运行设备
            version: 版本号

        Returns:
            部署信息
        """
        global _deployment_counter, _deployments

        try:
            # 检查是否已部署
            existing = self._get_running_deployment(model_id)
            if existing:
                return {
                    "success": False,
                    "error": f"Model {model_id} already deployed",
                    "deployment_id": existing.get("deployment_id"),
                    "port": existing.get("port")
                }

            model_format = self._normalize_model_format(model_format, model_path)
            task_kind = self._normalize_task_kind(task_kind)
            backend = backend or "onnxruntime"
            if model_format != "onnx":
                return {"success": False, "error": f"Unsupported model_format: {model_format}"}
            if backend != "onnxruntime":
                return {"success": False, "error": f"Unsupported backend: {backend}"}

            # 下载模型到本地
            local_model_path = self._local_model_path(model_id, model_path, model_format)
            if not os.path.exists(local_model_path):
                logger.info(
                    f"Downloading model {model_id} from S3: {model_path}")
                os.makedirs(os.path.dirname(local_model_path), exist_ok=True)
                download_from_s3(model_path, local_model_path,
                                 self.s3_config.models_bucket_name)
            logger.info(
                "Deploy artifact prepared: "
                f"model_id={model_id}, "
                f"s3_model_path={model_path}, "
                f"local_model_path={local_model_path}, "
                f"file_size_bytes={self._file_size_bytes(local_model_path)}, "
                f"sha256={self._file_sha256(local_model_path)}, "
                f"task_kind={task_kind}, "
                f"class_count={len(class_names or [])}, "
                f"class_names={list(class_names or [])}"
            )

            # 启动运行时
            instance = runtime_manager.deploy_model(
                model_id, local_model_path, device, task_kind, backend, class_names)
            if not instance:
                return {
                    "success": False,
                    "error": runtime_manager.last_error or "Failed to start runtime",
                }

            # 生成本地部署 ID
            _deployment_counter += 1
            deployment_id = _deployment_counter

            # 记录部署信息
            deployment_info = {
                "deployment_id": deployment_id,
                "model_id": model_id,
                "model_path": model_path,
                "version": version,
                "status": 1,  # running
                "port": instance.port,
                "pid": instance.pid,
                "device": device,
                "model_format": model_format,
                "task_kind": task_kind,
                "backend": backend,
            }
            _deployments[model_id] = deployment_info

            # 通过 MQ 发送部署成功消息（让主服务写入数据库）
            publish_model_deployed(model_id, deployment_info, SERVICE_NAME)

            return {
                "success": True,
                "deployment_id": deployment_id,
                "model_id": model_id,
                "port": instance.port,
                "status": "running",
                "model_format": model_format,
                "task_kind": task_kind,
                "backend": backend,
            }

        except Exception as e:
            logger.error(f"Deploy failed: {e}")
            return {"success": False, "error": str(e)}

    def _normalize_model_format(self, model_format: str, model_path: str) -> str:
        value = (model_format or "").strip().lower()
        if value:
            return value
        suffix = PurePosixPath(model_path).suffix.lower().lstrip(".")
        return suffix or "onnx"

    def _normalize_task_kind(self, task_kind: str) -> str:
        value = (task_kind or "detection_bbox").strip().lower()
        if value == "detection":
            return "detection_bbox"
        return value

    def _local_model_path(self, model_id: int, model_path: str, model_format: str) -> str:
        suffix = PurePosixPath(model_path).suffix.lower()
        if not suffix:
            suffix = f".{model_format}"
        return os.path.join(self.config.model_cache_dir, f"model_{model_id}{suffix}")

    def _get_running_deployment(self, model_id: int) -> Optional[Dict[str, Any]]:
        """获取正在运行的部署"""
        deployment = _deployments.get(model_id)
        if deployment:
            instance = runtime_manager.get_instance(model_id)
            if instance and instance.is_running():
                return deployment
            else:
                # 实例已停止，清理记录
                del _deployments[model_id]
        return None

    def _file_sha256(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _file_size_bytes(self, file_path: str) -> int:
        return int(os.path.getsize(file_path))

    def undeploy(self, model_id: int) -> Dict[str, Any]:
        """
        卸载模型

        Args:
            model_id: 模型ID

        Returns:
            操作结果
        """
        global _deployments

        try:
            deployment = _deployments.pop(model_id, None)
            instance = runtime_manager.get_instance(model_id)
            deployment_id = (deployment or {}).get("deployment_id") or 0

            # 卸载内存中的模型会话
            success = runtime_manager.undeploy_model(model_id)

            if not deployment and not instance:
                logger.warning(
                    f"Model {model_id} has no local deployment state; clearing remote deploy status only"
                )

            # 通过 MQ 发送卸载消息
            publish_model_undeployed(model_id, deployment_id, SERVICE_NAME)

            return {
                "success": success,
                "deployment_id": deployment_id,
                "message": (
                    "Deployment stopped"
                    if deployment or instance
                    else "Deployment state cleared"
                ) if success else "Failed to stop deployment"
            }

        except Exception as e:
            logger.error(f"Undeploy failed: {e}")
            return {"success": False, "error": str(e)}

    def get_deployments(self) -> List[Dict[str, Any]]:
        """获取所有部署（本地维护的状态）"""
        result = []

        for model_id, deployment in list(_deployments.items()):
            instance = runtime_manager.get_instance(model_id)
            is_running = instance.is_running() if instance else False

            if not is_running:
                # 清理已停止的部署
                del _deployments[model_id]
                continue

            result.append({
                "deployment_id": deployment.get("deployment_id"),
                "model_id": model_id,
                "model_path": deployment.get("model_path"),
                "version": deployment.get("version"),
                "status": "running" if is_running else "stopped",
                "port": deployment.get("port"),
                "device": deployment.get("device"),
                "model_format": deployment.get("model_format"),
                "task_kind": deployment.get("task_kind"),
                "backend": deployment.get("backend"),
            })

        return result

    def predict(
        self,
        model_id: int,
        image_data: bytes,
        inference_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        路由推理请求到对应的内存会话
        """
        instance = runtime_manager.get_instance(model_id)
        if not instance:
            return {"success": False, "error": f"Model {model_id} not deployed"}

        if not instance.is_running():
            return {"success": False, "error": f"Model {model_id} runtime not running"}

        try:
            logger.info(
                f"[predict-request] model_id={model_id}, mode=bytes, "
                f"payload_bytes={len(image_data)}, params={inference_params or {}}"
            )
            result = instance.predict(image_data, inference_params=inference_params)
            logger.info(
                f"[predict-response] model_id={model_id}, success={result.get('success')}, "
                f"result_count={len(result.get('results') or [])}, error={result.get('error')}"
            )
            return result
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {"success": False, "error": str(e)}

    def predict_base64(
        self,
        model_id: int,
        image_base64: str,
        inference_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """使用 base64 图像进行推理"""
        instance = runtime_manager.get_instance(model_id)
        if not instance:
            return {"success": False, "error": f"Model {model_id} not deployed"}

        if not instance.is_running():
            return {"success": False, "error": f"Model {model_id} runtime not running"}

        try:
            logger.info(
                f"[predict-request] model_id={model_id}, mode=base64, "
                f"payload_chars={len(image_base64 or '')}, params={inference_params or {}}"
            )
            result = instance.predict_base64(image_base64, inference_params=inference_params)
            logger.info(
                f"[predict-response] model_id={model_id}, success={result.get('success')}, "
                f"result_count={len(result.get('results') or [])}, error={result.get('error')}"
            )
            return result
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {"success": False, "error": str(e)}

    def predict_url(
        self,
        model_id: int,
        image_url: str,
        inference_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """使用 URL 图像进行推理"""
        instance = runtime_manager.get_instance(model_id)
        if not instance:
            return {"success": False, "error": f"Model {model_id} not deployed"}

        if not instance.is_running():
            return {"success": False, "error": f"Model {model_id} runtime not running"}

        try:
            logger.info(
                f"[predict-request] model_id={model_id}, mode=url, "
                f"url={image_url}, params={inference_params or {}}"
            )
            result = instance.predict_url(image_url, inference_params=inference_params)
            logger.info(
                f"[predict-response] model_id={model_id}, success={result.get('success')}, "
                f"result_count={len(result.get('results') or [])}, error={result.get('error')}"
            )
            return result
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {"success": False, "error": str(e)}

    def health_check(self, model_id: int) -> Dict[str, Any]:
        """检查部署健康状态"""
        instance = runtime_manager.get_instance(model_id)
        if not instance:
            return {"healthy": False, "error": "Model not deployed"}

        is_healthy = instance.health_check()
        return {
            "healthy": is_healthy,
            "model_id": model_id,
            "port": instance.port,
            "pid": instance.pid,
            "status": instance.status,
            "task_kind": instance.task_kind,
            "backend": instance.backend,
            "device": instance.device,
            "error": None if is_healthy else instance.last_error,
        }


# 全局部署服务实例
deploy_service = DeployService()
