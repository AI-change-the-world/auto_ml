"""推理服务 - 统一代理到 model_deploy"""
from typing import Optional

from loguru import logger
from requests import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BadRequestException, NotFoundException
from app.config.settings import get_settings
from app.utils.http_client import HttpClient
from app.modules.deploy import crud as deploy_crud

from .schemas import (
    InferenceHealthResponse,
    InferencePredictResponse,
)


class InferenceService:
    def __init__(self):
        settings = get_settings()
        self.deploy_url = settings.model_deploy.base_url
        self.http_client = HttpClient(
            base_url=self.deploy_url,
            timeout=settings.model_deploy.timeout,
        )

    async def close(self):
        await self.http_client.close()

    async def predict(
        self,
        db: AsyncSession,
        model_id: int,
        file_name: str,
        file_bytes: bytes,
        content_type: Optional[str] = None,
    ) -> InferencePredictResponse:
        model = await self._get_deployed_model(db, model_id)
        response = await self.http_client.post(
            f"/predict/{model_id}",
            files={
                "file": (
                    file_name or "image.jpg",
                    file_bytes,
                    content_type or "application/octet-stream",
                )
            },
        )
        payload = self._parse_backend_response(response, "predict")
        return self._build_predict_response(payload, model)

    async def predict_base64(
        self,
        db: AsyncSession,
        model_id: int,
        image_base64: str,
    ) -> InferencePredictResponse:
        model = await self._get_deployed_model(db, model_id)
        response = await self.http_client.post(
            f"/predict/{model_id}/base64",
            json={"image": image_base64},
        )
        payload = self._parse_backend_response(response, "predict/base64")
        return self._build_predict_response(payload, model)

    async def get_health(
        self,
        db: AsyncSession,
        model_id: int,
    ) -> InferenceHealthResponse:
        model = await deploy_crud.get_model_by_id(db, model_id)
        if not model:
            raise NotFoundException(f"Model {model_id} not found")

        detail = None
        backend_healthy = False
        if model.is_deployed:
            try:
                response = await self.http_client.get(f"/deploy/{model_id}/health")
                if response.status_code == 200:
                    detail = response.json()
                    backend_healthy = bool(detail.get("healthy", False))
                else:
                    detail = {
                        "healthy": False,
                        "error": response.text or f"status={response.status_code}",
                    }
            except Exception as exc:
                detail = {
                    "healthy": False,
                    "error": str(exc),
                }
                logger.warning(f"Failed to fetch inference health for model {model_id}: {exc}")

        return InferenceHealthResponse(
            model_id=model.id,
            model_name=model.name,
            task_kind=self._normalize_task_kind(model.model_type),
            backend=(detail or {}).get("backend") if isinstance(detail, dict) else None,
            is_deployed=bool(model.is_deployed),
            backend_healthy=backend_healthy,
            deployment_port=model.deployment_port,
            deployment_device=model.deployment_device,
            deployment_version=model.deployment_version,
            detail=detail,
        )

    async def _get_deployed_model(self, db: AsyncSession, model_id: int):
        model = await deploy_crud.get_model_by_id(db, model_id)
        if not model:
            raise NotFoundException(f"Model {model_id} not found")
        if not model.is_deployed:
            raise BadRequestException(f"Model {model_id} is not deployed")
        return model

    def _parse_backend_response(self, response: Response, operation: str) -> dict:
        try:
            payload = response.json()
        except Exception as exc:
            raise BadRequestException(
                f"Invalid response from deploy service during {operation}: {exc}"
            ) from exc

        if response.status_code != 200:
            detail = payload.get("detail") if isinstance(payload, dict) else None
            raise BadRequestException(
                f"Deploy service {operation} failed: {detail or response.text}"
            )
        if not isinstance(payload, dict):
            raise BadRequestException(
                f"Deploy service {operation} returned unexpected payload"
            )
        return payload

    def _build_predict_response(self, payload: dict, model) -> InferencePredictResponse:
        success = bool(payload.get("success"))
        error = payload.get("error")
        raw = None if success else payload
        task_kind = payload.get("task_kind") or self._normalize_task_kind(model.model_type)
        return InferencePredictResponse(
            success=success,
            model_id=model.id,
            model_name=model.name,
            task_kind=task_kind,
            backend=payload.get("backend"),
            device=payload.get("device") or model.deployment_device,
            results=payload.get("results") or [],
            image_width=payload.get("image_width"),
            image_height=payload.get("image_height"),
            error=error,
            raw=raw,
        )

    def _normalize_task_kind(self, model_type: str | None) -> str:
        if model_type == "detection":
            return "detection_bbox"
        return model_type or "detection_bbox"


async def get_inference_service():
    service = InferenceService()
    try:
        yield service
    finally:
        await service.close()
