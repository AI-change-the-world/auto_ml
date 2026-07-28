"""标注 CRUD"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Annotation, AnnotationCollaborator, AnnotationRecord, AnnotationSampleAssignment


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


async def get_annotations(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 10,
    keyword: str = None,
    dataset_id: int | None = None,
) -> tuple[List[Annotation], int]:
    conditions = [Annotation.is_deleted == False]
    if keyword:
        conditions.append(Annotation.name.ilike(f"%{keyword}%"))
    if dataset_id is not None:
        conditions.append(Annotation.dataset_id == dataset_id)

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


async def get_annotation_records_by_sample_ids(
    db: AsyncSession,
    annotation_id: int,
    sample_item_ids: list[int],
) -> List[AnnotationRecord]:
    if not sample_item_ids:
        return []
    stmt = (
        select(AnnotationRecord)
        .where(
            AnnotationRecord.annotation_id == annotation_id,
            AnnotationRecord.sample_item_id.in_(sample_item_ids),
            AnnotationRecord.is_deleted == False,
        )
        .order_by(AnnotationRecord.sample_item_id.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


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


# ============ Annotation Collaboration CRUD ============

async def count_annotation_collaborators(db: AsyncSession, annotation_id: int) -> int:
    stmt = (
        select(func.count())
        .select_from(AnnotationCollaborator)
        .where(
            AnnotationCollaborator.annotation_id == annotation_id,
            AnnotationCollaborator.is_deleted == False,
        )
    )
    return int((await db.execute(stmt)).scalar() or 0)


async def create_annotation_collaborator(db: AsyncSession, **kwargs) -> AnnotationCollaborator:
    collaborator = AnnotationCollaborator(**kwargs)
    db.add(collaborator)
    await db.flush()
    await db.refresh(collaborator)
    return collaborator


async def get_annotation_collaborator_by_token(
    db: AsyncSession,
    annotation_id: int,
    token: str,
) -> Optional[AnnotationCollaborator]:
    stmt = select(AnnotationCollaborator).where(
        AnnotationCollaborator.annotation_id == annotation_id,
        AnnotationCollaborator.token == token,
        AnnotationCollaborator.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_annotation_collaborator(
    db: AsyncSession,
    collaborator_id: int,
    **kwargs,
) -> Optional[AnnotationCollaborator]:
    stmt = select(AnnotationCollaborator).where(
        AnnotationCollaborator.id == collaborator_id,
        AnnotationCollaborator.is_deleted == False,
    )
    result = await db.execute(stmt)
    collaborator = result.scalar_one_or_none()
    if not collaborator:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(collaborator, key, value)
    await db.flush()
    await db.refresh(collaborator)
    return collaborator


async def create_annotation_assignment(db: AsyncSession, **kwargs) -> AnnotationSampleAssignment:
    assignment = AnnotationSampleAssignment(**kwargs)
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)
    return assignment


async def get_annotation_assignment(
    db: AsyncSession,
    annotation_id: int,
    sample_item_id: int,
) -> Optional[AnnotationSampleAssignment]:
    stmt = select(AnnotationSampleAssignment).where(
        AnnotationSampleAssignment.annotation_id == annotation_id,
        AnnotationSampleAssignment.sample_item_id == sample_item_id,
        AnnotationSampleAssignment.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_annotation_assignment_for_update(
    db: AsyncSession,
    annotation_id: int,
    sample_item_id: int,
) -> Optional[AnnotationSampleAssignment]:
    stmt = (
        select(AnnotationSampleAssignment)
        .where(
            AnnotationSampleAssignment.annotation_id == annotation_id,
            AnnotationSampleAssignment.sample_item_id == sample_item_id,
            AnnotationSampleAssignment.is_deleted == False,
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_annotation_assignment(
    db: AsyncSession,
    assignment_id: int,
    **kwargs,
) -> Optional[AnnotationSampleAssignment]:
    stmt = select(AnnotationSampleAssignment).where(
        AnnotationSampleAssignment.id == assignment_id,
        AnnotationSampleAssignment.is_deleted == False,
    )
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    if not assignment:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(assignment, key, value)
    await db.flush()
    await db.refresh(assignment)
    return assignment


async def get_annotation_assignments_by_collaborator(
    db: AsyncSession,
    annotation_id: int,
    collaborator_id: int,
    offset: int = 0,
    limit: int = 100,
) -> tuple[List[AnnotationSampleAssignment], int]:
    conditions = [
        AnnotationSampleAssignment.annotation_id == annotation_id,
        AnnotationSampleAssignment.collaborator_id == collaborator_id,
        AnnotationSampleAssignment.is_deleted == False,
        AnnotationSampleAssignment.status != "released",
    ]
    count_stmt = select(func.count()).select_from(AnnotationSampleAssignment).where(*conditions)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = (
        select(AnnotationSampleAssignment)
        .where(*conditions)
        .order_by(AnnotationSampleAssignment.sample_item_id.asc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), int(total)


async def count_active_annotation_assignments(
    db: AsyncSession,
    annotation_id: int,
    now: datetime,
) -> int:
    stmt = (
        select(func.count())
        .select_from(AnnotationSampleAssignment)
        .where(
            AnnotationSampleAssignment.annotation_id == annotation_id,
            AnnotationSampleAssignment.is_deleted == False,
            AnnotationSampleAssignment.status.in_(["assigned", "in_progress"]),
            AnnotationSampleAssignment.lease_expires_at > now,
        )
    )
    return int((await db.execute(stmt)).scalar() or 0)
