"""部署服务 - 与 model_deploy 通信"""
from typing import List, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import NotFoundException, BadRequestException
from app.config.settings import get_settings
from app.utils.http_client import HttpClient
from . import crud
from .schemas import (
    DeployRequest,
    RenameModelRequest,
    AvailableModelResponse,
    DeployStatusResponse,
)


class DeployService:
    def __init__(self):
        settings = get_settings()
        self.deploy_url = settings.model_deploy.base_url
        self.http_client = HttpClient(
            base_url=self.deploy_url,
            timeout=settings.model_deploy.timeout,
        )

    async def list_models(self, db: AsyncSession, page: int = 1, page_size: int = 10, deployed_only: bool = None) -> tuple[List[AvailableModelResponse], int]:
        offset = (page - 1) * page_size
        items, total = await crud.get_available_models(db, offset, page_size, deployed_only)
        return [AvailableModelResponse.model_validate(item) for item in items], total

    async def deploy_model(self, db: AsyncSession, data: DeployRequest) -> DeployStatusResponse:
        """部署模型"""
        model = await crud.get_model_by_id(db, data.model_id)
        if not model:
            raise NotFoundException(f"Model {data.model_id} not found")

        if model.is_deployed:
            raise BadRequestException(
                f"Model {data.model_id} is already deployed")

        if not model.onnx_model_path:
            raise BadRequestException(
                f"Model {data.model_id} has no ONNX artifact; enable ONNX export before deployment"
            )

        # 调用 model_deploy 服务
        try:
            deploy_request = {
                "model_id": data.model_id,
                "model_path": model.onnx_model_path,
                "model_format": "onnx",
                "task_kind": self._normalize_task_kind(model.model_type),
                "backend": "onnxruntime",
                "device": data.device,
                "version": data.version,
            }

            response = await self.http_client.post("/deploy", json=deploy_request)
            if response.status_code != 200:
                raise BadRequestException(
                    f"Failed to deploy model: {response.text}")
            payload = response.json()
            if not payload.get("success", False):
                raise BadRequestException(
                    payload.get("error") or f"Failed to deploy model {data.model_id}"
                )

            logger.info(f"Deploy request sent for model {data.model_id}")

        except Exception as e:
            logger.error(f"Failed to communicate with model_deploy: {e}")
            raise BadRequestException(f"Deploy service unavailable: {e}")

        # 返回当前状态（实际状态通过 MQ 更新）
        return DeployStatusResponse(
            model_id=data.model_id,
            is_deployed=False,  # 等待 MQ 消息更新
            deployment_id=None,
            port=None,
            version=data.version,
            device=data.device,
        )

    async def undeploy_model(self, db: AsyncSession, model_id: int) -> DeployStatusResponse:
        """卸载模型"""
        model = await crud.get_model_by_id(db, model_id)
        if not model:
            raise NotFoundException(f"Model {model_id} not found")

        if not model.is_deployed:
            raise BadRequestException(f"Model {model_id} is not deployed")

        # 调用 model_deploy 服务
        try:
            response = await self.http_client.post(f"/undeploy/{model_id}")
            if response.status_code != 200:
                raise BadRequestException(
                    f"Failed to undeploy model: {response.text}")
            payload = response.json()
            if not payload.get("success", False):
                raise BadRequestException(
                    payload.get("error") or f"Failed to undeploy model {model_id}"
                )

            logger.info(f"Undeploy request sent for model {model_id}")

        except Exception as e:
            logger.error(f"Failed to communicate with model_deploy: {e}")
            raise BadRequestException(f"Deploy service unavailable: {e}")

        return DeployStatusResponse(
            model_id=model_id,
            is_deployed=True,  # 等待 MQ 消息更新
            deployment_id=model.deployment_id,
            port=model.deployment_port,
            version=model.deployment_version,
            device=model.deployment_device,
        )

    async def rename_model(
        self,
        db: AsyncSession,
        model_id: int,
        data: RenameModelRequest,
    ) -> AvailableModelResponse:
        model = await crud.get_model_by_id(db, model_id)
        if not model:
            raise NotFoundException(f"Model {model_id} not found")

        name = data.name.strip()
        if not name:
            raise BadRequestException("Model name cannot be empty")

        updated = await crud.update_model_name(db, model, name)
        return AvailableModelResponse.model_validate(updated)

    def _normalize_task_kind(self, model_type: str | None) -> str:
        if model_type in {"detection_obb", "classification", "segmentation"}:
            return model_type
        if model_type in {"detection", "detection_bbox", None, ""}:
            return "detection_bbox"
        return str(model_type)

    async def get_deploy_status(self, db: AsyncSession, model_id: int) -> DeployStatusResponse:
        """获取部署状态"""
        model = await crud.get_model_by_id(db, model_id)
        if not model:
            raise NotFoundException(f"Model {model_id} not found")

        return DeployStatusResponse(
            model_id=model_id,
            is_deployed=model.is_deployed,
            deployment_id=model.deployment_id,
            port=model.deployment_port,
            version=model.deployment_version,
            device=model.deployment_device,
        )


def get_deploy_service() -> DeployService:
    return DeployService()
