"""
数据集 CRUD 操作
"""
from typing import List, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Dataset, Asset, SampleItem


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


# ============ Asset / SampleItem CRUD ============

async def create_asset(db: AsyncSession, **kwargs) -> Asset:
    asset = Asset(**kwargs)
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return asset


async def get_asset_by_id(db: AsyncSession, asset_id: int) -> Optional[Asset]:
    stmt = select(Asset).where(
        Asset.id == asset_id,
        Asset.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_sample_item(db: AsyncSession, **kwargs) -> SampleItem:
    item = SampleItem(**kwargs)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def get_sample_item_by_id(db: AsyncSession, sample_item_id: int) -> Optional[SampleItem]:
    stmt = select(SampleItem).where(
        SampleItem.id == sample_item_id,
        SampleItem.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_sample_item_by_key(
    db: AsyncSession,
    dataset_id: int,
    item_key: str,
) -> Optional[SampleItem]:
    stmt = select(SampleItem).where(
        SampleItem.dataset_id == dataset_id,
        SampleItem.item_key == item_key,
        SampleItem.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_sample_items(
    db: AsyncSession,
    dataset_id: int,
    offset: int = 0,
    limit: int = 100,
    item_type: Optional[str] = None,
) -> tuple[List[SampleItem], int]:
    conditions = [
        SampleItem.dataset_id == dataset_id,
        SampleItem.is_deleted == False,
    ]
    if item_type:
        conditions.append(SampleItem.item_type == item_type)

    count_stmt = select(func.count()).select_from(SampleItem).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()
    stmt = (
        select(SampleItem)
        .where(*conditions)
        .order_by(SampleItem.sort_order.asc(), SampleItem.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def get_sample_item_count(db: AsyncSession, dataset_id: int) -> int:
    stmt = (
        select(func.count())
        .select_from(SampleItem)
        .where(
            SampleItem.dataset_id == dataset_id,
            SampleItem.is_deleted == False,
        )
    )
    result = await db.execute(stmt)
    return result.scalar()


async def update_sample_item(db: AsyncSession, sample_item_id: int, **kwargs) -> Optional[SampleItem]:
    item = await get_sample_item_by_id(db, sample_item_id)
    if not item:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(item, key, value)
    await db.flush()
    await db.refresh(item)
    return item


async def delete_sample_item(db: AsyncSession, sample_item_id: int) -> bool:
    stmt = (
        update(SampleItem)
        .where(SampleItem.id == sample_item_id)
        .values(is_deleted=True)
    )
    result = await db.execute(stmt)
    return result.rowcount > 0

