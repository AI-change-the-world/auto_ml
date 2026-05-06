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
    FilePreviewResponse, FileContentResponse,
    SampleItemCreate, SampleItemUpdate, SampleItemResponse,
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


@router.get("/{dataset_id}/samples", response_model=Result[PageResult[SampleItemResponse]], summary="获取样本列表")
async def list_sample_items(
    dataset_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    item_type: str = Query(default=None),
    keyword: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    items, total = await service.list_sample_items(db, dataset_id, page, page_size, item_type, keyword)
    return Result.ok(PageResult.create(items, total, page, page_size))


@router.post("/{dataset_id}/samples", response_model=Result[SampleItemResponse], summary="创建样本")
async def create_sample_item(
    dataset_id: int,
    data: SampleItemCreate,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    result = await service.create_sample_item(db, dataset_id, data)
    return Result.ok(result, "Sample item created successfully")


@router.put("/{dataset_id}/samples/{sample_item_id}", response_model=Result[SampleItemResponse], summary="更新样本")
async def update_sample_item(
    dataset_id: int,
    sample_item_id: int,
    data: SampleItemUpdate,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    result = await service.update_sample_item(db, dataset_id, sample_item_id, data)
    return Result.ok(result, "Sample item updated successfully")


@router.delete("/{dataset_id}/samples/{sample_item_id}", response_model=Result, summary="删除样本")
async def delete_sample_item(
    dataset_id: int,
    sample_item_id: int,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    await service.delete_sample_item(db, dataset_id, sample_item_id)
    return Result.ok(message="Sample item deleted successfully")


@router.get("/{dataset_id}/samples/{sample_item_id}/preview", response_model=Result[FilePreviewResponse], summary="预览样本资源")
async def preview_sample(
    dataset_id: int,
    sample_item_id: int,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    """预览样本关联资源（获取预签名 URL）"""
    result = await service.preview_sample(db, dataset_id, sample_item_id)
    return Result.ok(result)


@router.get("/{dataset_id}/samples/{sample_item_id}/content", response_model=Result[FileContentResponse], summary="读取样本文本内容")
async def get_sample_content(
    dataset_id: int,
    sample_item_id: int,
    db: AsyncSession = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    """读取样本关联文本资源内容"""
    result = await service.get_sample_content(db, dataset_id, sample_item_id)
    return Result.ok(result)
