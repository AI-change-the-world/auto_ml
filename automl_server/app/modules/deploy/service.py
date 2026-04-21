"""部署服务 - 与 model_deploy 通信"""
import json
from datetime import datetime, timedelta
from typing import Any, List, Optional
from loguru import logger
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import NotFoundException, BadRequestException
from app.config.settings import get_settings
from app.db.models import ModelInferenceLog
from app.utils.http_client import HttpClient
from . import crud
from .schemas import (
    DeployRequest,
    RenameModelRequest,
    AvailableModelResponse,
    DeployStatusResponse,
    DeploymentDetailResponse,
    DeploymentOverviewItem,
    DeploymentOverviewResponse,
    DeploymentOverviewSummary,
    DeploymentRuntimeStatus,
    ModelInferenceActivityResponse,
    ModelInferenceLogResponse,
    ModelInferenceMetricsResponse,
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

    async def get_deployment_overview(
        self,
        db: AsyncSession,
        deployed_only: bool = False,
    ) -> DeploymentOverviewResponse:
        items, _ = await crud.get_available_models(db, 0, 200, None)
        runtime_map = await self._fetch_runtime_deployments()

        overview_items: list[DeploymentOverviewItem] = []
        for item in items:
            runtime_deployment = runtime_map.get(item.id)
            runtime_status = (
                await self._resolve_runtime_status(item.id, runtime_deployment)
                if item.is_deployed or runtime_deployment
                else DeploymentRuntimeStatus(status="offline", healthy=False, detail=None)
            )
            is_active = self._is_runtime_active(runtime_status)
            if deployed_only and not is_active:
                continue

            overview_items.append(
                DeploymentOverviewItem(
                    model_id=item.id,
                    model_name=item.name,
                    model_type=item.model_type,
                    task_id=item.task_id,
                    dataset_id=item.dataset_id,
                    deployment_id=self._deployment_value(is_active, item.deployment_id, runtime_deployment.get("deployment_id") if runtime_deployment else None),
                    deployment_port=self._deployment_value(is_active, item.deployment_port, runtime_deployment.get("port") if runtime_deployment else None),
                    deployment_version=self._deployment_value(is_active, item.deployment_version, runtime_deployment.get("version") if runtime_deployment else None),
                    deployment_device=self._deployment_value(is_active, item.deployment_device, runtime_deployment.get("device") if runtime_deployment else None),
                    is_deployed=is_active,
                    deployed_at=item.deployed_at,
                    inference_count=int(getattr(item, "inference_count", 0) or 0),
                    last_inference_at=getattr(item, "last_inference_at", None),
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    runtime_status=runtime_status,
                )
            )

        overview_items.sort(
            key=lambda current: (
                0 if current.is_deployed else 1,
                -(current.deployed_at.timestamp() if current.deployed_at else 0),
                -current.model_id,
            )
        )

        summary = DeploymentOverviewSummary(
            total_models=len(overview_items),
            active_deployments=sum(1 for item in overview_items if item.is_deployed),
            healthy_deployments=sum(
                1 for item in overview_items
                if item.is_deployed and item.runtime_status.healthy
            ),
            total_inference_calls=sum(item.inference_count for item in overview_items),
        )
        return DeploymentOverviewResponse(summary=summary, items=overview_items)

    async def deploy_model(self, db: AsyncSession, data: DeployRequest) -> DeployStatusResponse:
        """部署模型"""
        model = await crud.get_model_by_id(db, data.model_id)
        if not model:
            raise NotFoundException(f"Model {data.model_id} not found")

        runtime_map = await self._fetch_runtime_deployments()
        runtime_deployment = runtime_map.get(model.id)
        runtime_status = (
            await self._resolve_runtime_status(model.id, runtime_deployment)
            if model.is_deployed or runtime_deployment
            else DeploymentRuntimeStatus(status="offline", healthy=False, detail=None)
        )
        if self._is_runtime_active(runtime_status):
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
                "class_names": self._parse_classes(getattr(model, "class_names", None)),
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
            model = await crud.update_model_deployment_state(
                db,
                model,
                is_deployed=True,
                deployment_id=payload.get("deployment_id"),
                deployment_port=payload.get("port"),
                deployment_version=data.version,
                deployment_device=data.device,
                deployed_at=datetime.now(),
            )

            logger.info(f"Deploy request sent for model {data.model_id}")

        except Exception as e:
            logger.error(f"Failed to communicate with model_deploy: {e}")
            raise BadRequestException(f"Deploy service unavailable: {e}")

        return DeployStatusResponse(
            model_id=data.model_id,
            is_deployed=True,
            deployment_id=model.deployment_id,
            port=model.deployment_port,
            version=data.version,
            device=data.device,
        )

    async def undeploy_model(self, db: AsyncSession, model_id: int) -> DeployStatusResponse:
        """卸载模型"""
        model = await crud.get_model_by_id(db, model_id)
        if not model:
            raise NotFoundException(f"Model {model_id} not found")

        runtime_map = await self._fetch_runtime_deployments()
        runtime_deployment = runtime_map.get(model.id)
        runtime_status = (
            await self._resolve_runtime_status(model.id, runtime_deployment)
            if model.is_deployed or runtime_deployment
            else DeploymentRuntimeStatus(status="offline", healthy=False, detail=None)
        )
        if not model.is_deployed and not self._is_runtime_active(runtime_status):
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
            model = await crud.update_model_deployment_state(
                db,
                model,
                is_deployed=False,
                deployment_id=None,
                deployment_port=None,
                deployment_version=None,
                deployment_device=None,
            )

            logger.info(f"Undeploy request sent for model {model_id}")

        except Exception as e:
            logger.error(f"Failed to communicate with model_deploy: {e}")
            raise BadRequestException(f"Deploy service unavailable: {e}")

        return DeployStatusResponse(
            model_id=model_id,
            is_deployed=False,
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

    def _parse_classes(self, raw_classes: Optional[str]) -> list[str]:
        if not raw_classes:
            return []
        try:
            parsed = json.loads(raw_classes)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
        return [item.strip() for item in raw_classes.split(",") if item.strip()]

    async def get_deploy_status(self, db: AsyncSession, model_id: int) -> DeployStatusResponse:
        """获取部署状态"""
        model = await crud.get_model_by_id(db, model_id)
        if not model:
            raise NotFoundException(f"Model {model_id} not found")

        runtime_map = await self._fetch_runtime_deployments()
        runtime_deployment = runtime_map.get(model.id)
        runtime_status = (
            await self._resolve_runtime_status(model.id, runtime_deployment)
            if model.is_deployed or runtime_deployment
            else DeploymentRuntimeStatus(status="offline", healthy=False, detail=None)
        )
        is_active = self._is_runtime_active(runtime_status)
        return DeployStatusResponse(
            model_id=model_id,
            is_deployed=is_active,
            deployment_id=self._deployment_value(is_active, model.deployment_id, runtime_deployment.get("deployment_id") if runtime_deployment else None),
            port=self._deployment_value(is_active, model.deployment_port, runtime_deployment.get("port") if runtime_deployment else None),
            version=self._deployment_value(is_active, model.deployment_version, runtime_deployment.get("version") if runtime_deployment else None),
            device=self._deployment_value(is_active, model.deployment_device, runtime_deployment.get("device") if runtime_deployment else None),
        )

    async def get_model_inference_activity(
        self,
        db: AsyncSession,
        model_id: int,
        limit: int = 20,
    ) -> ModelInferenceActivityResponse:
        model = await crud.get_model_by_id(db, model_id)
        if not model:
            raise NotFoundException(f"Model {model_id} not found")

        logs, _ = await crud.list_inference_logs(db, model_id, 0, limit)
        metrics = await self._build_model_metrics(db, model_id, model)
        return ModelInferenceActivityResponse(
            metrics=metrics,
            logs=[ModelInferenceLogResponse.model_validate(item) for item in logs],
        )

    async def get_deployment_detail(
        self,
        db: AsyncSession,
        model_id: int,
    ) -> DeploymentDetailResponse:
        model = await crud.get_model_by_id(db, model_id)
        if not model:
            raise NotFoundException(f"Model {model_id} not found")

        runtime_map = await self._fetch_runtime_deployments()
        runtime_deployment = runtime_map.get(model.id)
        runtime_status = (
            await self._resolve_runtime_status(model.id, runtime_deployment)
            if model.is_deployed or runtime_deployment
            else DeploymentRuntimeStatus(status="offline", healthy=False, detail=None)
        )
        is_active = self._is_runtime_active(runtime_status)
        item = DeploymentOverviewItem(
            model_id=model.id,
            model_name=model.name,
            model_type=model.model_type,
            task_id=model.task_id,
            dataset_id=model.dataset_id,
            deployment_id=self._deployment_value(is_active, model.deployment_id, runtime_deployment.get("deployment_id") if runtime_deployment else None),
            deployment_port=self._deployment_value(is_active, model.deployment_port, runtime_deployment.get("port") if runtime_deployment else None),
            deployment_version=self._deployment_value(is_active, model.deployment_version, runtime_deployment.get("version") if runtime_deployment else None),
            deployment_device=self._deployment_value(is_active, model.deployment_device, runtime_deployment.get("device") if runtime_deployment else None),
            is_deployed=is_active,
            deployed_at=model.deployed_at,
            inference_count=int(getattr(model, "inference_count", 0) or 0),
            last_inference_at=getattr(model, "last_inference_at", None),
            created_at=model.created_at,
            updated_at=model.updated_at,
            runtime_status=runtime_status,
        )
        metrics = await self._build_model_metrics(db, model_id, model)
        return DeploymentDetailResponse(item=item, metrics=metrics)

    async def _build_model_metrics(
        self,
        db: AsyncSession,
        model_id: int,
        model,
    ) -> ModelInferenceMetricsResponse:
        stats_stmt = select(
            func.coalesce(func.sum(case((ModelInferenceLog.success == True, 1), else_=0)), 0),
            func.coalesce(func.sum(case((ModelInferenceLog.success == False, 1), else_=0)), 0),
            func.avg(ModelInferenceLog.duration_ms),
            func.coalesce(
                func.sum(
                    case(
                        (ModelInferenceLog.created_at >= datetime.now() - timedelta(hours=24), 1),
                        else_=0,
                    )
                ),
                0,
            ),
        ).where(
            ModelInferenceLog.model_id == model_id,
            ModelInferenceLog.is_deleted == False,
        )
        success_count, failure_count, avg_duration_ms, last_24h_count = (await db.execute(stats_stmt)).one()
        return ModelInferenceMetricsResponse(
            model_id=model_id,
            inference_count=int(getattr(model, "inference_count", 0) or 0),
            last_inference_at=getattr(model, "last_inference_at", None),
            success_count=int(success_count or 0),
            failure_count=int(failure_count or 0),
            avg_duration_ms=float(avg_duration_ms) if avg_duration_ms is not None else None,
            last_24h_count=int(last_24h_count or 0),
        )

    async def _fetch_runtime_deployments(self) -> dict[int, dict[str, Any]]:
        try:
            response = await self.http_client.get("/deployments")
            if response.status_code != 200:
                logger.warning(f"Failed to fetch runtime deployments: status={response.status_code}, body={response.text}")
                return {}
            payload = response.json()
            if not isinstance(payload, list):
                return {}

            runtime_map: dict[int, dict[str, Any]] = {}
            for item in payload:
                if not isinstance(item, dict):
                    continue
                model_id = item.get("model_id")
                if isinstance(model_id, int):
                    runtime_map[model_id] = item
            return runtime_map
        except Exception as exc:
            logger.warning(f"Failed to fetch runtime deployments: {exc}")
            return {}

    async def _resolve_runtime_status(
        self,
        model_id: int,
        runtime_deployment: Optional[dict[str, Any]] = None,
    ) -> DeploymentRuntimeStatus:
        try:
            response = await self.http_client.get(f"/deploy/{model_id}/health")
            if response.status_code == 200:
                payload = response.json()
                if isinstance(payload, dict):
                    return DeploymentRuntimeStatus(
                        status=self._normalize_runtime_status(payload.get("status"), payload.get("healthy")),
                        backend=payload.get("backend"),
                        task_kind=payload.get("task_kind"),
                        healthy=bool(payload.get("healthy")),
                        detail=payload,
                    )
        except Exception as exc:
            logger.warning(f"Failed to fetch deployment health for model {model_id}: {exc}")

        if runtime_deployment:
            return DeploymentRuntimeStatus(
                status=self._normalize_runtime_status(runtime_deployment.get("status"), True),
                backend=runtime_deployment.get("backend"),
                task_kind=runtime_deployment.get("task_kind"),
                healthy=bool(runtime_deployment.get("healthy", False)),
                detail=runtime_deployment,
            )

        return DeploymentRuntimeStatus(status="offline", healthy=False, detail=None)

    def _is_runtime_active(self, runtime_status: DeploymentRuntimeStatus) -> bool:
        return runtime_status.status == "running"

    def _normalize_runtime_status(self, status: Any, healthy: Any = None) -> str:
        if isinstance(status, str) and status.strip():
            value = status.strip().lower()
            return "running" if value in {"1", "running", "healthy", "ok"} else value
        if isinstance(status, (int, float)):
            return "running" if int(status) == 1 else str(status)
        return "running" if bool(healthy) else "offline"

    def _deployment_value(self, is_active: bool, primary: Any, secondary: Any) -> Any:
        if not is_active:
            return None
        return self._coalesce_value(secondary, primary)

    def _coalesce_value(self, primary: Any, secondary: Any) -> Any:
        return primary if primary not in (None, "", []) else secondary


def get_deploy_service() -> DeployService:
    return DeployService()
