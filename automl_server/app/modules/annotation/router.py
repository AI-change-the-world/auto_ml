"""标注 API 路由"""
import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.common import Result, PageResult
from app.config.database import get_db
from .schemas import (
    AnnotationAssistRequest,
    AnnotationAssistPipelineResponse,
    AnnotationAssistResponse,
    AnnotationCreate,
    AnnotationRecordBatchQuery,
    AnnotationRecordResponse,
    AnnotationRecordSave,
    AnnotationTypeDefinitionResponse,
    AnnotationUpdate,
    AnnotationResponse,
)
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


@router.get("/types", response_model=Result[list[AnnotationTypeDefinitionResponse]], summary="获取支持的标注类型")
async def list_annotation_types(
    service: AnnotationService = Depends(get_annotation_service),
):
    return Result.ok(service.list_annotation_types())


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


@router.get("/{annotation_id}/records", response_model=Result[PageResult[AnnotationRecordResponse]], summary="获取标注记录")
async def list_annotation_records(
    annotation_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    records, total = await service.list_annotation_records(db, annotation_id, page, page_size)
    return Result.ok(PageResult.create(records, total, page, page_size))


@router.post("/{annotation_id}/records/by-samples", response_model=Result[list[AnnotationRecordResponse]], summary="按样本批量获取标注记录")
async def list_annotation_records_by_sample_ids(
    annotation_id: int,
    data: AnnotationRecordBatchQuery,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    records = await service.list_annotation_records_by_sample_ids(db, annotation_id, data.sample_item_ids)
    return Result.ok(records)


@router.get("/{annotation_id}/export/dpo", summary="导出 DPO 标注结果")
async def export_dpo_records(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    items = await service.export_dpo_records(db, annotation_id)
    lines = [json.dumps(item.model_dump(mode="json"), ensure_ascii=False) for item in items]
    file_name = f"dpo_annotation_{annotation_id}.jsonl"
    return Response(
        content=("\n".join(lines)).encode("utf-8"),
        media_type="application/jsonl; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
        },
    )


@router.post("/{annotation_id}/records", response_model=Result[AnnotationRecordResponse], summary="保存标注记录")
async def save_annotation_record(
    annotation_id: int,
    data: AnnotationRecordSave,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    record = await service.save_annotation_record(db, annotation_id, data)
    return Result.ok(record, "Annotation record saved")


@router.post("/{annotation_id}/assist/current", response_model=Result[AnnotationAssistResponse], summary="辅助标注当前图片")
async def assist_current_annotation(
    annotation_id: int,
    data: AnnotationAssistRequest,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.assist_current_file(db, annotation_id, data)
    return Result.ok(result)


@router.get("/{annotation_id}/assist/pipelines", response_model=Result[list[AnnotationAssistPipelineResponse]], summary="获取可用辅助标注 Pipeline")
async def list_assist_pipelines(
    annotation_id: int,
    shape: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.list_assist_pipelines(db, annotation_id, shape=shape)
    return Result.ok(result)
