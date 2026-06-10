"""标注 API 路由"""
import asyncio
import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.common import Result, PageResult
from app.config.database import get_db
from app.modules.ai_pipeline.service import AiPipelineService, get_ai_pipeline_service
from app.modules.ai_pipeline.schemas import AiPipelineBindingResponse
from .schemas import (
    AnnotationAssistRequest,
    AnnotationAssistPipelineDetailResponse,
    AnnotationAssistPipelineResponse,
    AnnotationAssistResponse,
    AnnotationCreate,
    AnnotationCollaborationClaimRequest,
    AnnotationCollaborationClaimResponse,
    AnnotationCollaborationSamplesResponse,
    AnnotationCollaborationSessionRequest,
    AnnotationCollaborationSessionResponse,
    AnnotationCollaborationStatsResponse,
    AnnotationCollaboratorSummaryResponse,
    AnnotationPresenceHeartbeatRequest,
    AnnotationPresenceLeaveRequest,
    AnnotationRecordBatchQuery,
    AnnotationRecordResponse,
    AnnotationRecordSave,
    AnnotationSummaryResponse,
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


@router.get("/summary", response_model=Result[AnnotationSummaryResponse], summary="获取首页标注摘要")
async def get_annotation_summary(
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.get_home_summary(db)
    return Result.ok(result)


@router.get(
    "/assist/pipelines/platform",
    response_model=Result[list[AnnotationAssistPipelineDetailResponse]],
    summary="获取平台辅助标注 Pipeline 列表",
)
async def list_platform_assist_pipelines(
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    try:
        result = await asyncio.wait_for(
            service.list_home_platform_assist_pipeline_details(db),
            timeout=5,
        )
    except Exception as exc:
        logger.warning(f"Failed to load platform assist pipelines: {exc}")
        result = []
    return Result.ok(result)


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
    items, export_name = await service.export_dpo_records(db, annotation_id)
    lines = [json.dumps(item.model_dump(mode="json"), ensure_ascii=False) for item in items]
    file_name = f"{export_name}_{annotation_id}.jsonl"
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


@router.post(
    "/{annotation_id}/presence/heartbeat",
    response_model=Result[list[AnnotationCollaboratorSummaryResponse]],
    summary="更新标注项目在线状态",
)
async def heartbeat_annotation_presence(
    annotation_id: int,
    data: AnnotationPresenceHeartbeatRequest,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.heartbeat_annotation_presence(db, annotation_id, data)
    return Result.ok(result)


@router.post(
    "/{annotation_id}/presence/leave",
    response_model=Result[list[AnnotationCollaboratorSummaryResponse]],
    summary="退出标注项目在线状态",
)
async def leave_annotation_presence(
    annotation_id: int,
    data: AnnotationPresenceLeaveRequest,
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.leave_annotation_presence(annotation_id, data.participant_id)
    return Result.ok(result)


@router.post(
    "/{annotation_id}/collaboration/session",
    response_model=Result[AnnotationCollaborationSessionResponse],
    summary="创建或恢复协作标注会话",
)
async def create_collaboration_session(
    annotation_id: int,
    data: AnnotationCollaborationSessionRequest,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.create_collaboration_session(db, annotation_id, data)
    return Result.ok(result)


@router.post(
    "/{annotation_id}/collaboration/claim",
    response_model=Result[AnnotationCollaborationClaimResponse],
    summary="领取协作标注样本",
)
async def claim_collaboration_samples(
    annotation_id: int,
    data: AnnotationCollaborationClaimRequest,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.claim_collaboration_samples(db, annotation_id, data)
    return Result.ok(result)


@router.get(
    "/{annotation_id}/collaboration/samples",
    response_model=Result[AnnotationCollaborationSamplesResponse],
    summary="获取当前协作者样本",
)
async def list_collaboration_samples(
    annotation_id: int,
    collaborator_token: str = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.list_collaboration_samples(
        db,
        annotation_id,
        collaborator_token,
        page,
        page_size,
    )
    return Result.ok(result)


@router.get(
    "/{annotation_id}/collaboration/stats",
    response_model=Result[AnnotationCollaborationStatsResponse],
    summary="获取协作标注进度",
)
async def get_collaboration_stats(
    annotation_id: int,
    collaborator_token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    result = await service.get_collaboration_stats(db, annotation_id, collaborator_token)
    return Result.ok(result)


@router.post("/{annotation_id}/assist/current", response_model=Result[AnnotationAssistResponse], summary="辅助标注当前图片")
async def assist_current_annotation(
    annotation_id: int,
    data: AnnotationAssistRequest,
    db: AsyncSession = Depends(get_db),
    service: AnnotationService = Depends(get_annotation_service),
):
    logger.info(
        "Assist annotation api request annotation_id={} sample_item_id={} pipeline_id={} binding_id={} shape={}",
        annotation_id,
        data.sample_item_id,
        data.pipeline_id,
        data.binding_id,
        data.shape,
    )
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


@router.get(
    "/{annotation_id}/ai-pipeline-bindings",
    response_model=Result[list[AiPipelineBindingResponse]],
    summary="获取标注项目 AI Pipeline 绑定",
)
async def list_annotation_ai_pipeline_bindings(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    items, _ = await service.list_bindings(
        db,
        page=1,
        page_size=100,
        binding_type="annotation_project",
        binding_target_id=annotation_id,
    )
    return Result.ok(items)
