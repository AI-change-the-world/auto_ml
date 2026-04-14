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
    )).scalar() or 0

    # 数据集文件（图片）数量
    image_count = (await db.execute(
        select(func.coalesce(func.sum(Dataset.count), 0)).select_from(
            Dataset).where(Dataset.is_deleted == False)
    )).scalar() or 0

    # 标注项目数量
    annotation_count = (await db.execute(
        select(func.count()).select_from(Annotation).where(
            Annotation.is_deleted == False)
    )).scalar() or 0

    # 任务统计
    total_tasks = (await db.execute(
        select(func.count()).select_from(Task).where(Task.is_deleted == False)
    )).scalar() or 0

    running_tasks = (await db.execute(
        select(func.count()).select_from(Task).where(
            Task.is_deleted == False, Task.status == 1)
    )).scalar() or 0

    completed_tasks = (await db.execute(
        select(func.count()).select_from(Task).where(
            Task.is_deleted == False, Task.status == 3)
    )).scalar() or 0

    # 模型统计
    total_models = (await db.execute(
        select(func.count()).select_from(AvailableModel).where(
            AvailableModel.is_deleted == False)
    )).scalar() or 0

    deployed_models = (await db.execute(
        select(func.count()).select_from(AvailableModel).where(
            AvailableModel.is_deleted == False,
            AvailableModel.is_deployed == True
        )
    )).scalar() or 0

    # 最近的标注项目（最多5个）
    recent_annotations_result = await db.execute(
        select(Annotation.id, Annotation.name,
               Annotation.annotation_type, Annotation.created_at)
        .where(Annotation.is_deleted == False)
        .order_by(Annotation.created_at.desc())
        .limit(5)
    )
    recent_annotations = [
        {"id": r.id, "name": r.name, "annotation_type": r.annotation_type,
         "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in recent_annotations_result.fetchall()
    ]

    # 最近的数据集（最多5个）
    recent_datasets_result = await db.execute(
        select(Dataset.id, Dataset.name, Dataset.count,
               Dataset.data_type, Dataset.created_at)
        .where(Dataset.is_deleted == False)
        .order_by(Dataset.created_at.desc())
        .limit(5)
    )
    recent_datasets = [
        {"id": r.id, "name": r.name, "count": r.count or 0,
         "data_type": r.data_type,
         "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in recent_datasets_result.fetchall()
    ]

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
        "recent_annotations": recent_annotations,
        "recent_datasets": recent_datasets,
    })
