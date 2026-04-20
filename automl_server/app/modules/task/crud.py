"""任务 CRUD"""
from typing import List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Task, TaskLog, TaskSource, BaseModels


async def create_task(db: AsyncSession, **kwargs) -> Task:
    task = Task(**kwargs)
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def get_task_by_id(db: AsyncSession, task_id: int) -> Optional[Task]:
    stmt = select(Task).where(Task.id == task_id, Task.is_deleted == False)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_task_sources(db: AsyncSession, task_id: int, sources: list[dict]) -> list[TaskSource]:
    rows: list[TaskSource] = []
    for source in sources:
        row = TaskSource(task_id=task_id, **source)
        db.add(row)
        rows.append(row)
    await db.flush()
    return rows


async def get_task_sources(db: AsyncSession, task_id: int) -> list[TaskSource]:
    stmt = (
        select(TaskSource)
        .where(TaskSource.task_id == task_id, TaskSource.is_deleted == False)
        .order_by(TaskSource.source_order.asc(), TaskSource.id.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_task_sources_by_task_ids(db: AsyncSession, task_ids: list[int]) -> dict[int, list[TaskSource]]:
    if not task_ids:
        return {}
    stmt = (
        select(TaskSource)
        .where(TaskSource.task_id.in_(task_ids), TaskSource.is_deleted == False)
        .order_by(TaskSource.task_id.asc(), TaskSource.source_order.asc(), TaskSource.id.asc())
    )
    result = await db.execute(stmt)
    grouped: dict[int, list[TaskSource]] = {}
    for row in result.scalars().all():
        grouped.setdefault(row.task_id, []).append(row)
    return grouped


async def get_tasks(db: AsyncSession, offset: int = 0, limit: int = 10, status: int = None) -> tuple[List[Task], int]:
    conditions = [Task.is_deleted == False]
    if status is not None:
        conditions.append(Task.status == status)

    count_stmt = select(func.count()).select_from(Task).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()

    stmt = select(Task).where(
        *conditions).order_by(Task.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def update_task_status(db: AsyncSession, task_id: int, status: int, error_message: str = None) -> bool:
    update_data = {"status": status}
    if error_message:
        update_data["error_message"] = error_message
    stmt = update(Task).where(Task.id == task_id).values(**update_data)
    result = await db.execute(stmt)
    return result.rowcount > 0


async def get_task_logs(db: AsyncSession, task_id: int, offset: int = 0, limit: int = 100) -> tuple[List[TaskLog], int]:
    conditions = [TaskLog.task_id == task_id, TaskLog.is_deleted == False]
    count_stmt = select(func.count()).select_from(TaskLog).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()

    stmt = select(TaskLog).where(
        *conditions).order_by(TaskLog.created_at.asc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def get_base_models(db: AsyncSession) -> List[BaseModels]:
    stmt = select(BaseModels).where(
        BaseModels.is_deleted == False).order_by(BaseModels.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_task(db: AsyncSession, task_id: int) -> bool:
    await db.execute(
        update(TaskSource)
        .where(TaskSource.task_id == task_id, TaskSource.is_deleted == False)
        .values(is_deleted=True)
    )
    stmt = (
        update(Task)
        .where(Task.id == task_id, Task.is_deleted == False)
        .values(is_deleted=True)
    )
    result = await db.execute(stmt)
    return result.rowcount > 0
