"""标注 CRUD"""
from typing import List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Annotation, AnnotationRecord


async def create_annotation(db: AsyncSession, **kwargs) -> Annotation:
    ann = Annotation(**kwargs)
    db.add(ann)
    await db.flush()
    await db.refresh(ann)
    return ann


async def get_annotation_by_id(db: AsyncSession, annotation_id: int) -> Optional[Annotation]:
    stmt = select(Annotation).where(Annotation.id ==
                                    annotation_id, Annotation.is_deleted == False)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_annotations(db: AsyncSession, offset: int = 0, limit: int = 10, keyword: str = None) -> tuple[List[Annotation], int]:
    conditions = [Annotation.is_deleted == False]
    if keyword:
        conditions.append(Annotation.name.ilike(f"%{keyword}%"))

    count_stmt = select(func.count()).select_from(
        Annotation).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()

    stmt = select(Annotation).where(
        *conditions).order_by(Annotation.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def update_annotation(db: AsyncSession, annotation_id: int, **kwargs) -> Optional[Annotation]:
    ann = await get_annotation_by_id(db, annotation_id)
    if not ann:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(ann, key, value)
    await db.flush()
    await db.refresh(ann)
    return ann


async def delete_annotation(db: AsyncSession, annotation_id: int) -> bool:
    stmt = update(Annotation).where(Annotation.id ==
                                    annotation_id).values(is_deleted=True)
    result = await db.execute(stmt)
    return result.rowcount > 0


# ============ AnnotationRecord CRUD ============

async def create_annotation_record(db: AsyncSession, **kwargs) -> AnnotationRecord:
    record = AnnotationRecord(**kwargs)
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_annotation_record(
    db: AsyncSession,
    annotation_id: int,
    sample_item_id: int,
) -> Optional[AnnotationRecord]:
    stmt = select(AnnotationRecord).where(
        AnnotationRecord.annotation_id == annotation_id,
        AnnotationRecord.sample_item_id == sample_item_id,
        AnnotationRecord.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_annotation_records(
    db: AsyncSession,
    annotation_id: int,
    offset: int = 0,
    limit: int = 100,
) -> tuple[List[AnnotationRecord], int]:
    conditions = [
        AnnotationRecord.annotation_id == annotation_id,
        AnnotationRecord.is_deleted == False,
    ]
    count_stmt = select(func.count()).select_from(AnnotationRecord).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()
    stmt = (
        select(AnnotationRecord)
        .where(*conditions)
        .order_by(AnnotationRecord.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def update_annotation_record(
    db: AsyncSession,
    record_id: int,
    **kwargs,
) -> Optional[AnnotationRecord]:
    stmt = select(AnnotationRecord).where(
        AnnotationRecord.id == record_id,
        AnnotationRecord.is_deleted == False,
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if not record:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(record, key, value)
    await db.flush()
    await db.refresh(record)
    return record
