"""推理 API 路由"""
import json

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import Result
from app.common.exceptions import BadRequestException
from app.config.database import get_db

from .schemas import (
    InferenceBase64Request,
    InferenceParams,
    InferenceHealthResponse,
    InferencePredictResponse,
)
from .service import InferenceService, get_inference_service
from app.modules.system.guards import require_capability


router = APIRouter(prefix="/inference", tags=["模型推理"])


@router.post(
    "/models/{model_id}/predict",
    response_model=Result[InferencePredictResponse],
    summary="通过上传文件执行模型推理",
)
async def predict_model(
    model_id: int,
    request: Request,
    file: UploadFile = File(...),
    inference_params: str | None = Form(default=None),
    _: None = Depends(require_capability("deployment", "predict")),
    db: AsyncSession = Depends(get_db),
    service: InferenceService = Depends(get_inference_service),
):
    content = await file.read()
    parsed_params = None
    if inference_params:
        try:
            parsed_params = InferenceParams.model_validate(json.loads(inference_params))
        except Exception as exc:
            raise BadRequestException(f"invalid inference_params: {exc}") from exc
    result = await service.predict(
        db,
        model_id=model_id,
        file_name=file.filename or "image.jpg",
        file_bytes=content,
        content_type=file.content_type,
        inference_params=parsed_params,
        client_ip=request.client.host if request.client else None,
    )
    return Result.ok(result)


@router.post(
    "/models/{model_id}/predict/base64",
    response_model=Result[InferencePredictResponse],
    summary="通过 base64 图像执行模型推理",
)
async def predict_model_base64(
    model_id: int,
    data: InferenceBase64Request,
    request: Request,
    _: None = Depends(require_capability("deployment", "predict")),
    db: AsyncSession = Depends(get_db),
    service: InferenceService = Depends(get_inference_service),
):
    result = await service.predict_base64(
        db,
        model_id=model_id,
        image_base64=data.image,
        inference_params=data.inference_params,
        client_ip=request.client.host if request.client else None,
    )
    return Result.ok(result)


@router.get(
    "/models/{model_id}/health",
    response_model=Result[InferenceHealthResponse],
    summary="获取模型推理健康状态",
)
async def get_model_inference_health(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    service: InferenceService = Depends(get_inference_service),
):
    result = await service.get_health(db, model_id=model_id)
    return Result.ok(result)
