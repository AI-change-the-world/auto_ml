"""
数据集 CRUD 操作
"""
from typing import List, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Dataset, DatasetFile


async def create_dataset(db: AsyncSession, **kwargs) -> Dataset:
    """创建数据集"""
    dataset = Dataset(**kwargs)
    db.add(dataset)
    await db.flush()
    await db.refresh(dataset)
    return dataset


async def get_dataset_by_id(db: AsyncSession, dataset_id: int) -> Optional[Dataset]:
    """根据 ID 获取数据集"""
    stmt = select(Dataset).where(
        Dataset.id == dataset_id,
        Dataset.is_deleted == False
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_datasets(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 10,
    keyword: str = None
) -> tuple[List[Dataset], int]:
    """分页查询数据集"""
    # 基础查询条件
    conditions = [Dataset.is_deleted == False]
    
    if keyword:
        conditions.append(Dataset.name.ilike(f"%{keyword}%"))
    
    # 查询总数
    count_stmt = select(func.count()).select_from(Dataset).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()
    
    # 分页查询
    stmt = (
        select(Dataset)
        .where(*conditions)
        .order_by(Dataset.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    
    return items, total


async def update_dataset(db: AsyncSession, dataset_id: int, **kwargs) -> Optional[Dataset]:
    """更新数据集"""
    dataset = await get_dataset_by_id(db, dataset_id)
    if not dataset:
        return None
    
    for key, value in kwargs.items():
        if value is not None:
            setattr(dataset, key, value)
    
    await db.flush()
    await db.refresh(dataset)
    return dataset


async def delete_dataset(db: AsyncSession, dataset_id: int) -> bool:
    """软删除数据集"""
    stmt = (
        update(Dataset)
        .where(Dataset.id == dataset_id)
        .values(is_deleted=True)
    )
    result = await db.execute(stmt)
    return result.rowcount > 0


async def update_dataset_count(db: AsyncSession, dataset_id: int, count: int):
    """更新数据集文件数量"""
    stmt = (
        update(Dataset)
        .where(Dataset.id == dataset_id)
        .values(count=count)
    )
    await db.execute(stmt)


# ============ DatasetFile CRUD ============

async def create_dataset_file(db: AsyncSession, **kwargs) -> DatasetFile:
    """创建数据集文件"""
    file = DatasetFile(**kwargs)
    db.add(file)
    await db.flush()
    await db.refresh(file)
    return file


async def get_dataset_files(
    db: AsyncSession,
    dataset_id: int,
    offset: int = 0,
    limit: int = 100
) -> tuple[List[DatasetFile], int]:
    """获取数据集文件列表"""
    conditions = [
        DatasetFile.dataset_id == dataset_id,
        DatasetFile.is_deleted == False
    ]
    
    # 总数
    count_stmt = select(func.count()).select_from(DatasetFile).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()
    
    # 分页
    stmt = (
        select(DatasetFile)
        .where(*conditions)
        .order_by(DatasetFile.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    
    return items, total


async def get_dataset_file_count(db: AsyncSession, dataset_id: int) -> int:
    """获取数据集文件数量"""
    stmt = (
        select(func.count())
        .select_from(DatasetFile)
        .where(
            DatasetFile.dataset_id == dataset_id,
            DatasetFile.is_deleted == False
        )
    )
    result = await db.execute(stmt)
    return result.scalar()
