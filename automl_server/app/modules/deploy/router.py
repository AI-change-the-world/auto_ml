"""部署 API 路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.common import Result, PageResult
from app.config.database import get_db
from .schemas import (
    DeployRequest,
    RenameModelRequest,
    AvailableModelResponse,
    DeployStatusResponse,
)
from .service import get_deploy_service, DeployService

router = APIRouter(prefix="/deploy", tags=["模型部署"])


@router.get("/models", response_model=Result[PageResult[AvailableModelResponse]], summary="获取可用模型列表")
async def list_models(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    deployed_only: bool = Query(default=None),
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    items, total = await service.list_models(db, page, page_size, deployed_only)
    return Result.ok(PageResult.create(items, total, page, page_size))


@router.post("/{model_id}/deploy", response_model=Result[DeployStatusResponse], summary="部署模型")
async def deploy_model(
    model_id: int,
    device: str = Query(default="cpu"),
    version: str = Query(default="v1"),
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    data = DeployRequest(model_id=model_id, device=device, version=version)
    result = await service.deploy_model(db, data)
    return Result.ok(result, "Deploy request sent")


@router.post("/{model_id}/undeploy", response_model=Result[DeployStatusResponse], summary="卸载模型")
async def undeploy_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    result = await service.undeploy_model(db, model_id)
    return Result.ok(result, "Undeploy request sent")


@router.patch("/{model_id}/rename", response_model=Result[AvailableModelResponse], summary="重命名模型")
async def rename_model(
    model_id: int,
    data: RenameModelRequest,
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    result = await service.rename_model(db, model_id, data)
    return Result.ok(result, "Model renamed")


@router.get("/{model_id}/status", response_model=Result[DeployStatusResponse], summary="获取部署状态")
async def get_deploy_status(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    result = await service.get_deploy_status(db, model_id)
    return Result.ok(result)
