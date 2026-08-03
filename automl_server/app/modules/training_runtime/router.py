"""APIs for the custom training runtime's immutable package catalogs."""
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import Result
from app.config.database import get_db

from .schemas import (
    TrainingRuntimeCodePackageImportResponse,
    TrainingRuntimeCodePackageResponse,
    TrainingRuntimeModelPackageImportResponse,
    TrainingRuntimeModelPackageResponse,
)
from .service import TrainingRuntimeCatalogService, get_training_runtime_catalog_service


router = APIRouter(prefix="/training-runtime", tags=["自定义训练运行时"])


@router.get(
    "/code-packages",
    response_model=Result[list[TrainingRuntimeCodePackageResponse]],
    summary="获取自定义训练脚本包",
)
async def list_code_packages(
    include_disabled: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    service: TrainingRuntimeCatalogService = Depends(get_training_runtime_catalog_service),
):
    return Result.ok(await service.list_code_packages(db, include_disabled=include_disabled))


@router.post(
    "/code-packages/import",
    response_model=Result[TrainingRuntimeCodePackageImportResponse],
    summary="导入自定义训练脚本包",
)
async def import_code_package(
    file: UploadFile = File(..., description="包含 training_package.json 的 ZIP"),
    db: AsyncSession = Depends(get_db),
    service: TrainingRuntimeCatalogService = Depends(get_training_runtime_catalog_service),
):
    result = await service.import_code_package(
        db,
        archive_name=file.filename or "training-package.zip",
        archive_bytes=await file.read(),
    )
    return Result.ok(result, "Training code package imported")


@router.get(
    "/model-packages",
    response_model=Result[list[TrainingRuntimeModelPackageResponse]],
    summary="获取自定义训练模型包",
)
async def list_model_packages(
    include_disabled: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    service: TrainingRuntimeCatalogService = Depends(get_training_runtime_catalog_service),
):
    return Result.ok(await service.list_model_packages(db, include_disabled=include_disabled))


@router.post(
    "/model-packages/import",
    response_model=Result[TrainingRuntimeModelPackageImportResponse],
    summary="导入自定义训练模型包",
)
async def import_model_package(
    file: UploadFile = File(..., description="包含 training_model_package.json 的 ZIP"),
    db: AsyncSession = Depends(get_db),
    service: TrainingRuntimeCatalogService = Depends(get_training_runtime_catalog_service),
):
    result = await service.import_model_package(
        db,
        archive_name=file.filename or "training-model-package.zip",
        archive_bytes=await file.read(),
    )
    return Result.ok(result, "Training model package imported")
