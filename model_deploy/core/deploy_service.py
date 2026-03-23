"""
部署服务核心逻辑
处理模型的部署、卸载、推理路由等
"""
import os
from typing import Any, Dict, List, Optional

from db.base import get_sync_db
from db.crud import (
    create_deployment,
    get_all_deployments,
    get_available_model,
    get_deployment_by_model,
    update_deployment,
)
from core.runtime_manager import runtime_manager
from utils.config import download_from_s3, get_deploy_config
from utils.logger import logger


class DeployService:
    """部署服务"""

    def __init__(self):
        self.config = get_deploy_config()

    def deploy(
        self,
        model_id: int,
        device: str = "cpu",
        version: str = "v1"
    ) -> Dict[str, Any]:
        """
        部署模型

        Args:
            model_id: 模型ID
            device: 运行设备
            version: 版本号

        Returns:
            部署信息
        """
        db = get_sync_db()

        try:
            # 检查模型是否存在
            model = get_available_model(db, model_id)
            if not model:
                return {"success": False, "error": f"Model {model_id} not found"}

            # 检查是否已部署
            existing = get_deployment_by_model(db, model_id)
            if existing:
                return {
                    "success": False,
                    "error": f"Model {model_id} already deployed",
                    "deployment_id": existing.deployment_id,
                    "port": existing.port
                }

            # 下载模型
            model_local_path = os.path.join(
                self.config.model_cache_dir, model.save_path)
            if not os.path.exists(model_local_path):
                logger.info(f"Downloading model {model_id} from S3...")
                download_from_s3(
                    model.save_path,
                    model_local_path,
                    self.config.s3.models_bucket_name
                )

            # 启动运行时
            instance = runtime_manager.deploy_model(
                model_id, model_local_path, device)
            if not instance:
                return {"success": False, "error": "Failed to start runtime"}

            # 创建部署记录
            deployment_data = {
                "model_id": model_id,
                "model_name": model.base_model_name,
                "version": version,
                "status": 1,  # running
                "port": instance.port,
                "pid": instance.pid,
                "replicas": 1,
                "device": device,
            }
            deployment = create_deployment(db, deployment_data)

            return {
                "success": True,
                "deployment_id": deployment.deployment_id,
                "model_id": model_id,
                "port": instance.port,
                "status": "running"
            }

        except Exception as e:
            logger.error(f"Deploy failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def undeploy(self, deployment_id: int) -> Dict[str, Any]:
        """
        卸载模型

        Args:
            deployment_id: 部署ID

        Returns:
            操作结果
        """
        db = get_sync_db()

        try:
            from db.crud import get_deployment
            deployment = get_deployment(db, deployment_id)
            if not deployment:
                return {"success": False, "error": f"Deployment {deployment_id} not found"}

            # 停止运行时
            success = runtime_manager.undeploy_model(deployment.model_id)

            # 更新部署状态
            update_deployment(db, deployment_id, {"status": 2})  # stopped

            return {
                "success": success,
                "deployment_id": deployment_id,
                "message": "Deployment stopped" if success else "Failed to stop deployment"
            }

        except Exception as e:
            logger.error(f"Undeploy failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def get_deployments(self) -> List[Dict[str, Any]]:
        """获取所有部署"""
        db = get_sync_db()

        try:
            deployments = get_all_deployments(db)
            result = []

            for dep in deployments:
                # 检查实例状态
                instance = runtime_manager.get_instance(dep.model_id)
                is_running = instance.is_running() if instance else False

                result.append({
                    "deployment_id": dep.deployment_id,
                    "model_id": dep.model_id,
                    "model_name": dep.model_name,
                    "version": dep.version,
                    "status": "running" if is_running else "stopped",
                    "port": dep.port,
                    "device": dep.device,
                    "created_at": dep.created_at,
                })

            return result

        except Exception as e:
            logger.error(f"Get deployments failed: {e}")
            return []
        finally:
            db.close()

    def predict(self, model_id: int, image_data: bytes) -> Dict[str, Any]:
        """
        路由推理请求到对应的运行时实例

        Args:
            model_id: 模型ID
            image_data: 图像数据

        Returns:
            推理结果
        """
        import urllib.request
        import json

        instance = runtime_manager.get_instance(model_id)
        if not instance:
            return {"success": False, "error": f"Model {model_id} not deployed"}

        if not instance.is_running():
            return {"success": False, "error": f"Model {model_id} runtime not running"}

        try:
            # 转发请求到运行时服务
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
                    'Content-Type': f'multipart/form-data; boundary={boundary}'
                },
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                return result

        except Exception as e:
            logger.error(f"Prediction routing failed: {e}")
            return {"success": False, "error": str(e)}

    def predict_base64(self, model_id: int, image_base64: str) -> Dict[str, Any]:
        """
        使用 base64 图像进行推理

        Args:
            model_id: 模型ID
            image_base64: base64 编码的图像

        Returns:
            推理结果
        """
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
            "status": instance.status
        }


# 全局部署服务实例
deploy_service = DeployService()
