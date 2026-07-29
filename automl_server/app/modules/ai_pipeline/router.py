"""AI Pipeline 管理 API"""
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import PageResult, Result
from app.common.sse import create_sse_response
from app.config.database import get_db

from .schemas import (
    AiPipelineBindingCreate,
    AiPipelineCapabilityItem,
    AiPipelineModelResourceItem,
    AiPipelineProviderResourceItem,
    AiPipelineProviderResourceOption,
    AiPipelineProviderResourceCreate,
    AiPipelineProviderResourceUpdate,
    AiPipelineBindingResponse,
    AiPipelineBindingUpdate,
    AiPipelineTemplateCreate,
    AiPipelineTemplateDetail,
    AiPipelineTemplateDraftSave,
    AiPipelineTemplateListItem,
)
from .service import AiPipelineService, get_ai_pipeline_service
from .batch_schemas import (
    AiPipelineBatchRunCreate,
    AiPipelineBatchRunDetailResponse,
    AiPipelineBatchRunEventResponse,
    AiPipelineBatchRunItemResponse,
    AiPipelineBatchRunResponse,
    AiPipelineBatchScriptResponse,
    AiPipelineBatchScriptUpdate,
)
from .batch_service import BatchAnnotationService, get_batch_annotation_service
from .batch_stream import get_batch_run_stream_hub

router = APIRouter(prefix="/ai-pipeline", tags=["AI Pipeline"])


@router.get(
    "/batch-scripts",
    response_model=Result[list[AiPipelineBatchScriptResponse]],
    summary="获取批量自动标注脚本",
)
async def list_batch_scripts(
    include_disabled: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    return Result.ok(await service.list_scripts(db, include_disabled=include_disabled))


@router.get(
    "/batch-scripts/{script_key}",
    response_model=Result[AiPipelineBatchScriptResponse],
    summary="获取批量自动标注脚本详情",
)
async def get_batch_script(
    script_key: str,
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    return Result.ok(await service.get_script(db, script_key))


@router.post(
    "/batch-scripts/upload",
    response_model=Result[AiPipelineBatchScriptResponse],
    summary="上传批量自动标注脚本包",
)
async def upload_batch_script(
    file: UploadFile = File(..., description="ZIP 脚本包"),
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    file_bytes = await file.read()
    script = await service.upload_script(db, file.filename or "script.zip", file_bytes)
    return Result.ok(script, "Batch script uploaded")


@router.patch(
    "/batch-scripts/{script_key}",
    response_model=Result[AiPipelineBatchScriptResponse],
    summary="更新批量自动标注脚本配置",
)
async def update_batch_script(
    script_key: str,
    data: AiPipelineBatchScriptUpdate,
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    return Result.ok(await service.update_script(db, script_key, data), "Batch script updated")


@router.delete(
    "/batch-scripts/{script_key}",
    response_model=Result,
    summary="删除批量自动标注脚本",
)
async def delete_batch_script(
    script_key: str,
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    await service.delete_script(db, script_key)
    return Result.ok(message="Batch script deleted")


@router.post(
    "/batch-runs",
    response_model=Result[AiPipelineBatchRunResponse],
    summary="创建批量自动标注任务",
)
async def create_batch_run(
    data: AiPipelineBatchRunCreate,
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    run = await service.create_run(db, data)
    return Result.ok(run, "Batch annotation run created")


@router.get(
    "/batch-runs",
    response_model=Result[list[AiPipelineBatchRunResponse]],
    summary="获取批量自动标注任务列表",
)
async def list_batch_runs(
    dataset_id: Optional[int] = Query(default=None, gt=0),
    annotation_id: Optional[int] = Query(default=None, gt=0),
    script_key: Optional[str] = Query(default=None, min_length=1, max_length=128),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    runs = await service.list_runs(
        db,
        dataset_id=dataset_id,
        annotation_id=annotation_id,
        script_key=script_key,
        limit=limit,
    )
    return Result.ok(runs)


@router.get(
    "/batch-runs/{run_id}",
    response_model=Result[AiPipelineBatchRunDetailResponse],
    summary="获取批量自动标注任务详情",
)
async def get_batch_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    return Result.ok(await service.get_run(db, run_id))


@router.get(
    "/batch-runs/{run_id}/stream",
    summary="批量自动标注任务 SSE 事件流",
)
async def batch_run_stream(
    request: Request,
    run_id: str,
):
    hub = get_batch_run_stream_hub()
    subscriber_id, queue = await hub.subscribe(run_id)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=5)
                except asyncio.TimeoutError:
                    continue
                yield event.to_sse_payload()
        finally:
            await hub.unsubscribe(subscriber_id, run_id)

    return create_sse_response(event_generator())


@router.get(
    "/batch-runs/{run_id}/items",
    response_model=Result[PageResult[AiPipelineBatchRunItemResponse]],
    summary="获取批量自动标注样本结果",
)
async def list_batch_run_items(
    run_id: str,
    status: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    items, total = await service.list_items(
        db,
        run_id,
        status=status,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return Result.ok(PageResult.create(items, total, page, page_size))


@router.get(
    "/batch-runs/{run_id}/events",
    response_model=Result[list[AiPipelineBatchRunEventResponse]],
    summary="获取批量自动标注任务事件",
)
async def list_batch_run_events(
    run_id: str,
    after_id: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    latest: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    return Result.ok(
        await service.list_events(db, run_id, after_id=after_id, limit=limit, latest=latest)
    )


@router.post(
    "/batch-runs/{run_id}/cancel",
    response_model=Result[AiPipelineBatchRunResponse],
    summary="取消批量自动标注任务",
)
async def cancel_batch_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    return Result.ok(await service.cancel_run(db, run_id), "Batch annotation run canceled")


@router.post(
    "/batch-runs/{run_id}/resume",
    response_model=Result[AiPipelineBatchRunResponse],
    summary="继续执行等待中的批量自动标注任务",
)
async def resume_batch_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    service: BatchAnnotationService = Depends(get_batch_annotation_service),
):
    return Result.ok(await service.resume_run(db, run_id), "Batch annotation run re-dispatched")


@router.post(
    "/templates",
    response_model=Result[AiPipelineTemplateListItem],
    summary="创建 AI Pipeline 模板",
)
async def create_template(
    data: AiPipelineTemplateCreate,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.create_template(db, data)
    return Result.ok(result, "AI pipeline template created")


@router.get(
    "/templates",
    response_model=Result[PageResult[AiPipelineTemplateListItem]],
    summary="获取 AI Pipeline 模板列表",
)
async def list_templates(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    scene_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    items, total = await service.list_templates(
        db,
        page=page,
        page_size=page_size,
        scene_type=scene_type,
        status=status,
        keyword=keyword,
    )
    return Result.ok(PageResult.create(items, total, page, page_size))


@router.get(
    "/templates/{template_key}",
    response_model=Result[AiPipelineTemplateDetail],
    summary="获取 AI Pipeline 模板详情",
)
async def get_template_detail(
    template_key: str,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.get_template_detail(db, template_key)
    return Result.ok(result)


@router.put(
    "/templates/{template_key}",
    response_model=Result[AiPipelineTemplateDetail],
    summary="保存 AI Pipeline 模板定义",
)
async def save_template(
    template_key: str,
    data: AiPipelineTemplateDraftSave,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.save_template_definition(db, template_key, data)
    return Result.ok(result, "AI pipeline template saved")


@router.post(
    "/templates/{template_key}/disable",
    response_model=Result[AiPipelineTemplateDetail],
    summary="禁用 AI Pipeline 模板",
)
async def disable_template(
    template_key: str,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.disable_template(db, template_key)
    return Result.ok(result, "AI pipeline template disabled")


@router.delete(
    "/templates/{template_key}",
    response_model=Result,
    summary="删除 AI Pipeline 模板",
)
async def delete_template(
    template_key: str,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    await service.delete_template(db, template_key)
    return Result.ok(message="AI pipeline template deleted")


@router.get(
    "/capabilities",
    response_model=Result[list[AiPipelineCapabilityItem]],
    summary="获取 AI Pipeline 能力目录",
)
async def list_capabilities(
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.list_capabilities()
    return Result.ok(result)


@router.get(
    "/bindings",
    response_model=Result[PageResult[AiPipelineBindingResponse]],
    summary="获取 AI Pipeline 绑定列表",
)
async def list_bindings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    binding_type: Optional[str] = Query(default=None),
    binding_target_id: Optional[int] = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    items, total = await service.list_bindings(
        db,
        page=page,
        page_size=page_size,
        binding_type=binding_type,
        binding_target_id=binding_target_id,
    )
    return Result.ok(PageResult.create(items, total, page, page_size))


@router.post(
    "/bindings",
    response_model=Result[AiPipelineBindingResponse],
    summary="创建 AI Pipeline 绑定",
)
async def create_binding(
    data: AiPipelineBindingCreate,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.create_binding(db, data)
    return Result.ok(result, "AI pipeline binding created")


@router.put(
    "/bindings/{binding_id}",
    response_model=Result[AiPipelineBindingResponse],
    summary="更新 AI Pipeline 绑定",
)
async def update_binding(
    binding_id: int,
    data: AiPipelineBindingUpdate,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.update_binding(db, binding_id, data)
    return Result.ok(result, "AI pipeline binding updated")


@router.delete(
    "/bindings/{binding_id}",
    response_model=Result,
    summary="删除 AI Pipeline 绑定",
)
async def delete_binding(
    binding_id: int,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    await service.delete_binding(db, binding_id)
    return Result.ok(message="AI pipeline binding deleted")


@router.get(
    "/resources/models",
    response_model=Result[list[AiPipelineModelResourceItem]],
    summary="获取 AI Pipeline 可选模型资源",
)
async def list_model_resources(
    deployed_only: bool = Query(default=True),
    limit: int = Query(default=200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.list_model_resources(
        db,
        deployed_only=deployed_only,
        limit=limit,
    )
    return Result.ok(result)


@router.get(
    "/resources/providers",
    response_model=Result[list[AiPipelineProviderResourceOption]],
    summary="获取 AI Pipeline 可选 Provider 资源",
)
async def list_provider_resources(
    enabled_only: bool = Query(default=True),
    limit: int = Query(default=200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.list_provider_resource_options(
        db,
        enabled_only=enabled_only,
        limit=limit,
    )
    return Result.ok(result)


@router.get(
    "/provider-resources",
    response_model=Result[list[AiPipelineProviderResourceItem]],
    summary="获取 AI Pipeline Provider 资源管理列表",
)
async def list_provider_resource_items(
    enabled_only: bool = Query(default=False),
    limit: int = Query(default=200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.list_provider_resources(
        db,
        enabled_only=enabled_only,
        limit=limit,
    )
    return Result.ok(result)


@router.post(
    "/provider-resources",
    response_model=Result[AiPipelineProviderResourceItem],
    summary="创建 AI Pipeline Provider 资源",
)
async def create_provider_resource(
    data: AiPipelineProviderResourceCreate,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.create_provider_resource(db, data)
    return Result.ok(result, "AI pipeline provider resource created")


@router.put(
    "/provider-resources/{resource_id}",
    response_model=Result[AiPipelineProviderResourceItem],
    summary="更新 AI Pipeline Provider 资源",
)
async def update_provider_resource(
    resource_id: int,
    data: AiPipelineProviderResourceUpdate,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.update_provider_resource(db, resource_id, data)
    return Result.ok(result, "AI pipeline provider resource updated")


@router.delete(
    "/provider-resources/{resource_id}",
    response_model=Result,
    summary="删除 AI Pipeline Provider 资源",
)
async def delete_provider_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    service: AiPipelineService = Depends(get_ai_pipeline_service),
):
    await service.delete_provider_resource(db, resource_id)
    return Result.ok(message="AI pipeline provider resource deleted")
