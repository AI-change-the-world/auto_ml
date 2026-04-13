"""首页统计 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.common import Result
from app.config.database import get_db
from app.db.models import Dataset, DatasetFile, Annotation, Task, AvailableModel

router = APIRouter(prefix="/home", tags=["首页"])


@router.get("/stats", response_model=Result, summary="获取统计数据")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """获取首页统计数据"""

    # 数据集数量
    dataset_count = (await db.execute(
        select(func.count()).select_from(
            Dataset).where(Dataset.is_deleted == False)
    )).scalar()

    # 数据集文件（图片）数量
    image_count = (await db.execute(
        select(func.coalesce(func.sum(Dataset.count), 0)).select_from(
            Dataset).where(Dataset.is_deleted == False)
    )).scalar()

    # 标注项目数量
    annotation_count = (await db.execute(
        select(func.count()).select_from(Annotation).where(
            Annotation.is_deleted == False)
    )).scalar()

    # 任务统计
    total_tasks = (await db.execute(
        select(func.count()).select_from(Task).where(Task.is_deleted == False)
    )).scalar()

    running_tasks = (await db.execute(
        select(func.count()).select_from(Task).where(
            Task.is_deleted == False, Task.status == 1)
    )).scalar()

    completed_tasks = (await db.execute(
        select(func.count()).select_from(Task).where(
            Task.is_deleted == False, Task.status == 3)
    )).scalar()

    # 模型统计
    total_models = (await db.execute(
        select(func.count()).select_from(AvailableModel).where(
            AvailableModel.is_deleted == False)
    )).scalar()

    deployed_models = (await db.execute(
        select(func.count()).select_from(AvailableModel).where(
            AvailableModel.is_deleted == False,
            AvailableModel.is_deployed == True
        )
    )).scalar()

    return Result.ok({
        "datasets": dataset_count,
        "images": image_count,
        "annotations": annotation_count,
        "tasks": {
            "total": total_tasks,
            "running": running_tasks,
            "completed": completed_tasks,
        },
        "models": {
            "total": total_models,
            "deployed": deployed_models,
        },
    })
