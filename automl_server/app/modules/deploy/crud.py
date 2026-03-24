"""部署 CRUD"""
from typing import List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import AvailableModel


async def get_available_models(db: AsyncSession, offset: int = 0, limit: int = 10, deployed_only: bool = None) -> tuple[List[AvailableModel], int]:
    conditions = [AvailableModel.is_deleted == False]
    if deployed_only is not None:
        conditions.append(AvailableModel.is_deployed == deployed_only)

    count_stmt = select(func.count()).select_from(
        AvailableModel).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()

    stmt = select(AvailableModel).where(
        *conditions).order_by(AvailableModel.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def get_model_by_id(db: AsyncSession, model_id: int) -> Optional[AvailableModel]:
    stmt = select(AvailableModel).where(AvailableModel.id ==
                                        model_id, AvailableModel.is_deleted == False)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
