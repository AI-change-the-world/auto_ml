"""标注 API 路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.common import Result, PageResult
from app.config.database import get_db
from .schemas import AnnotationCreate, AnnotationUpdate, AnnotationResponse, AnnotationFileResponse, AnnotationFileSave
from .service import get_annotation_service, AnnotationService

router = APIRouter(prefix="/annotation", tags=["标注管理"])


@router.post("/new", response_model=Result[AnnotationResponse], summary="创建标注项目")
async def create_annotation(
    data: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.create_annotation(db, data)
    return Result.ok(result, "Annotation created successfully")


@router.get("/list", response_model=Result[PageResult[AnnotationResponse]], summary="查询标注项目列表")
async def list_annotations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    items, total = await service.list_annotations(db, page, page_size, keyword)
    return Result.ok(PageResult.create(items, total, page, page_size))


@router.get("/{annotation_id}", response_model=Result[AnnotationResponse], summary="获取标注项目详情")
async def get_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.get_annotation(db, annotation_id)
    return Result.ok(result)


@router.put("/{annotation_id}", response_model=Result[AnnotationResponse], summary="更新标注项目")
async def update_annotation(
    annotation_id: int,
    data: AnnotationUpdate,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.update_annotation(db, annotation_id, data)
    return Result.ok(result, "Annotation updated successfully")


@router.delete("/{annotation_id}", response_model=Result, summary="删除标注项目")
async def delete_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    await service.delete_annotation(db, annotation_id)
    return Result.ok(message="Annotation deleted successfully")


@router.post("/{annotation_id}/file", response_model=Result[int], summary="保存标注文件")
async def save_annotation_file(
    annotation_id: int,
    data: AnnotationFileSave,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    file_id = await service.save_annotation_file(db, annotation_id, data)
    return Result.ok(file_id, "Annotation file saved")


@router.get("/{annotation_id}/files", response_model=Result[PageResult[AnnotationFileResponse]], summary="获取标注文件列表")
async def get_annotation_files(
    annotation_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    files, total = await service.get_files(db, annotation_id, page, page_size)
    items = [AnnotationFileResponse.model_validate(f) for f in files]
    return Result.ok(PageResult.create(items, total, page, page_size))
