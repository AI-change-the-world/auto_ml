"""
数据集 API 路由
"""
from typing import List

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import Result, PageResult
from app.config.database import get_db
from .schemas import (
    DatasetCreate, DatasetUpdate, DatasetResponse,
    DatasetFileResponse, FilePreviewResponse
)
from .service import get_dataset_service, DatasetService

router = APIRouter(prefix="/dataset", tags=["数据集管理"])


@router.post("/new", response_model=Result[DatasetResponse], summary="创建数据集")
async def create_dataset(
    data: DatasetCreate,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    """创建新数据集"""
    result = await service.create_dataset(db, data)
    return Result.ok(result, "Dataset created successfully")


@router.get("/list", response_model=Result[PageResult[DatasetResponse]], summary="查询数据集列表")
async def list_datasets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    """分页查询数据集"""
    items, total = await service.list_datasets(db, page, page_size, keyword)
    page_result = PageResult.create(items, total, page, page_size)
    return Result.ok(page_result)


@router.get("/{dataset_id}", response_model=Result[DatasetResponse], summary="获取数据集详情")
async def get_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    """获取数据集详情"""
    result = await service.get_dataset(db, dataset_id)
    return Result.ok(result)


@router.put("/{dataset_id}", response_model=Result[DatasetResponse], summary="更新数据集")
async def update_dataset(
    dataset_id: int,
    data: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    """更新数据集"""
    result = await service.update_dataset(db, dataset_id, data)
    return Result.ok(result, "Dataset updated successfully")


@router.delete("/{dataset_id}", response_model=Result, summary="删除数据集")
async def delete_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    """删除数据集"""
    await service.delete_dataset(db, dataset_id)
    return Result.ok(message="Dataset deleted successfully")


@router.post("/{dataset_id}/upload", response_model=Result[int], summary="上传文件")
async def upload_files(
    dataset_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    """上传文件到数据集"""
    count = await service.upload_files(db, dataset_id, files)
    return Result.ok(count, f"Uploaded {count} files successfully")


@router.get("/{dataset_id}/files", response_model=Result[PageResult[DatasetFileResponse]], summary="获取文件列表")
async def get_files(
    dataset_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    """获取数据集文件列表"""
    files, total = await service.get_files(db, dataset_id, page, page_size)
    from .schemas import DatasetFileResponse
    items = [DatasetFileResponse.model_validate(f) for f in files]
    page_result = PageResult.create(items, total, page, page_size)
    return Result.ok(page_result)


@router.get("/{dataset_id}/preview", response_model=Result[FilePreviewResponse], summary="预览文件")
async def preview_file(
    dataset_id: int,
    file_name: str = Query(...),
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    """预览文件（获取预签名 URL）"""
    result = await service.preview_file(db, dataset_id, file_name)
    return Result.ok(result)
