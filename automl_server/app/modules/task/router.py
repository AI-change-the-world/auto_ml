"""任务 API 路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.common import Result, PageResult
from app.config.database import get_db
from .schemas import TaskCreate, TaskResponse, TaskLogResponse, BaseModelResponse, TrainerStatusResponse
from .service import get_task_service, TaskService

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


@router.get("/trainer/status", response_model=Result[TrainerStatusResponse], summary="获取训练服务状态")
async def get_trainer_status(
    service: TaskService = Depends(get_task_service),
):
    status = await service.get_trainer_status()
    return Result.ok(status)


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
