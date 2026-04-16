"""
部署服务核心逻辑
使用 RabbitMQ 发送状态更新，不直接写数据库
"""
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

            # 启动运行时
            instance = runtime_manager.deploy_model(
                model_id, local_model_path, device, task_kind, backend)
            if not instance:
                return {"success": False, "error": "Failed to start runtime"}

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
            deployment = _deployments.get(model_id)
            if not deployment:
                return {"success": False, "error": f"Model {model_id} not deployed"}

            deployment_id = deployment.get("deployment_id")

            # 停止运行时
            success = runtime_manager.undeploy_model(model_id)

            # 清理本地记录
            if model_id in _deployments:
                del _deployments[model_id]

            # 通过 MQ 发送卸载消息
            publish_model_undeployed(model_id, deployment_id, SERVICE_NAME)

            return {
                "success": success,
                "deployment_id": deployment_id,
                "message": "Deployment stopped" if success else "Failed to stop deployment"
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

    def predict(self, model_id: int, image_data: bytes) -> Dict[str, Any]:
        """
        路由推理请求到对应的运行时实例
        """
        import urllib.request
        import json

        instance = runtime_manager.get_instance(model_id)
        if not instance:
            return {"success": False, "error": f"Model {model_id} not deployed"}

        if not instance.is_running():
            return {"success": False, "error": f"Model {model_id} runtime not running"}

        try:
            url = f"http://localhost:{instance.port}/predict"

            # 构建 multipart 请求
            boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
            body = []
            body.append(f'--{boundary}'.encode())
            body.append(
                b'Content-Disposition: form-data; name="file"; filename="image.jpg"')
            body.append(b'Content-Type: image/jpeg')
            body.append(b'')
            body.append(image_data)
            body.append(f'--{boundary}--'.encode())

            req = urllib.request.Request(
                url,
                data=b'\r\n'.join(body),
                headers={
                    'Content-Type': f'multipart/form-data; boundary={boundary}'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                result.setdefault("task_kind", instance.task_kind)
                result.setdefault("backend", instance.backend)
                result.setdefault("device", instance.device)
                return result

        except Exception as e:
            logger.error(f"Prediction routing failed: {e}")
            return {"success": False, "error": str(e)}

    def predict_base64(self, model_id: int, image_base64: str) -> Dict[str, Any]:
        """使用 base64 图像进行推理"""
        import urllib.request
        import json

        instance = runtime_manager.get_instance(model_id)
        if not instance:
            return {"success": False, "error": f"Model {model_id} not deployed"}

        if not instance.is_running():
            return {"success": False, "error": f"Model {model_id} runtime not running"}

        try:
            url = f"http://localhost:{instance.port}/predict/base64"

            req = urllib.request.Request(
                url,
                data=json.dumps({"image": image_base64}).encode(),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                result.setdefault("task_kind", instance.task_kind)
                result.setdefault("backend", instance.backend)
                result.setdefault("device", instance.device)
                return result

        except Exception as e:
            logger.error(f"Prediction routing failed: {e}")
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
        }


# 全局部署服务实例
deploy_service = DeployService()
