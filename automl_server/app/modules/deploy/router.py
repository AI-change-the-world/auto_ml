"""部署 API 路由"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.common import Result, PageResult
from app.config.database import get_db
from .schemas import (
    DeployRequest,
    RenameModelRequest,
    AvailableModelResponse,
    DeploymentDetailResponse,
    DeploymentHomeSummaryResponse,
    DeployStatusResponse,
    DeploymentOverviewResponse,
    ModelInferenceActivityResponse,
    UploadOnnxModelRequest,
    UploadOnnxModelResponse,
)
from .service import get_deploy_service, DeployService

router = APIRouter(prefix="/deploy", tags=["模型部署"])


@router.get("/models", response_model=Result[PageResult[AvailableModelResponse]], summary="获取可用模型列表")
async def list_models(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=200),
    deployed_only: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    items, total = await service.list_models(db, page, page_size, deployed_only)
    return Result.ok(PageResult.create(items, total, page, page_size))


@router.get("/overview", response_model=Result[DeploymentOverviewResponse], summary="获取部署概览")
async def get_deployment_overview(
    deployed_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    result = await service.get_deployment_overview(db, deployed_only=deployed_only)
    return Result.ok(result)


@router.get("/summary", response_model=Result[DeploymentHomeSummaryResponse], summary="获取首页部署摘要")
async def get_deployment_summary(
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    result = await service.get_home_summary(db)
    return Result.ok(result)


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


@router.post(
    "/models/upload-onnx",
    response_model=Result[UploadOnnxModelResponse],
    summary="上传 ONNX 模型",
)
async def upload_onnx_model(
    name: str = Form(...),
    template: str = Form(...),
    class_names: str = Form(default="[]"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    data = UploadOnnxModelRequest(
        name=name,
        template=template,
        class_names=class_names,
    )
    file_bytes = await file.read()
    result = await service.upload_onnx_model(
        db,
        data=data,
        file_name=file.filename or "model.onnx",
        file_bytes=file_bytes,
    )
    return Result.ok(result, "ONNX model uploaded")


@router.get("/{model_id}/status", response_model=Result[DeployStatusResponse], summary="获取部署状态")
async def get_deploy_status(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    result = await service.get_deploy_status(db, model_id)
    return Result.ok(result)


@router.get("/{model_id}/detail", response_model=Result[DeploymentDetailResponse], summary="获取单实例部署详情")
async def get_deploy_detail(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    result = await service.get_deployment_detail(db, model_id)
    return Result.ok(result)


@router.get("/{model_id}/activity", response_model=Result[ModelInferenceActivityResponse], summary="获取单模型调用活动")
async def get_model_activity(
    model_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    service: DeployService = Depends(get_deploy_service),
):
    result = await service.get_model_inference_activity(db, model_id, limit=limit)
    return Result.ok(result)
