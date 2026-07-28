"""任务 API 路由"""
import asyncio
from contextlib import suppress

from fastapi import APIRouter, Depends, Query
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.common import Result, PageResult
from app.common.sse import create_sse_response
from app.config.database import get_db
from .schemas import (
    TaskCreate,
    TaskResponse,
    TaskLogResponse,
    BaseModelResponse,
    TaskSummaryResponse,
    TrainerStatusResponse,
    TrainingHistoryCandidateResponse,
    TrainingHistoryQuery,
)
from .service import get_task_service, TaskService
from .stream import StreamEvent, get_task_stream_hub

router = APIRouter(prefix="/task", tags=["任务管理"])


@router.post("/train", response_model=Result[TaskResponse], summary="创建训练任务")
async def create_train_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
):
    result = await service.create_task(db, data)
    return Result.ok(result, "Training task created")


@router.get("/list", response_model=Result[PageResult[TaskResponse]], summary="查询任务列表")
async def list_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: int = Query(default=None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
):
    items, total = await service.list_tasks(db, page, page_size, status)
    return Result.ok(PageResult.create(items, total, page, page_size))


@router.get("/base-models", response_model=Result[list[BaseModelResponse]], summary="获取基础模型列表")
async def get_base_models(
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
):
    models = await service.get_base_models(db)
    return Result.ok(models)


@router.post("/training-history", response_model=Result[list[TrainingHistoryCandidateResponse]], summary="查询历史训练候选")
async def get_training_history(
    data: TrainingHistoryQuery,
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
):
    result = await service.get_training_history_candidates(db, data)
    return Result.ok(result)


@router.get("/trainer/status", response_model=Result[TrainerStatusResponse], summary="获取训练服务状态")
async def get_trainer_status(
    service: TaskService = Depends(get_task_service),
):
    status = await service.get_trainer_status()
    return Result.ok(status)


@router.get("/summary", response_model=Result[TaskSummaryResponse], summary="获取首页任务摘要")
async def get_task_summary(
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
):
    result = await service.get_home_summary(db)
    return Result.ok(result)


@router.get("/stream", summary="任务 SSE 事件流")
async def task_stream(
    request: Request,
    task_id: int | None = Query(default=None, description="任务ID，不传则订阅全局任务事件"),
    service: TaskService = Depends(get_task_service),
):
    hub = get_task_stream_hub()
    subscriber_id, queue = await hub.subscribe(task_id=task_id)

    async def trainer_probe():
        last_payload = None
        while True:
            try:
                payload = (await service.get_trainer_status()).model_dump(mode="json")
                if payload != last_payload:
                    last_payload = payload
                    with suppress(asyncio.QueueFull):
                        queue.put_nowait(
                            StreamEvent(event="trainer_status", task_id=None, data={"trainer_status": payload})
                        )
            except Exception:
                pass
            await asyncio.sleep(5)

    async def event_generator():
        probe_task = None
        if task_id is None:
            probe_task = asyncio.create_task(trainer_probe())
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
            if probe_task is not None:
                probe_task.cancel()
                with suppress(asyncio.CancelledError):
                    await probe_task
            await hub.unsubscribe(subscriber_id, task_id=task_id)

    return create_sse_response(event_generator())


@router.get("/{task_id}", response_model=Result[TaskResponse], summary="获取任务详情")
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
):
    result = await service.get_task(db, task_id)
    return Result.ok(result)


@router.get("/{task_id}/logs", response_model=Result[PageResult[TaskLogResponse]], summary="获取任务日志")
async def get_task_logs(
    task_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
):
    logs, total = await service.get_task_logs(db, task_id, page, page_size)
    return Result.ok(PageResult.create(logs, total, page, page_size))


@router.delete("/{task_id}", response_model=Result, summary="删除任务")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    service: TaskService = Depends(get_task_service),
):
    await service.delete_task(db, task_id)
    return Result.ok(message="Task deleted")
