"""标注 CRUD"""
from typing import List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Annotation, AnnotationFile


async def create_annotation(db: AsyncSession, **kwargs) -> Annotation:
    ann = Annotation(**kwargs)
    db.add(ann)
    await db.flush()
    await db.refresh(ann)
    return ann


async def get_annotation_by_id(db: AsyncSession, annotation_id: int) -> Optional[Annotation]:
    stmt = select(Annotation).where(Annotation.id == annotation_id, Annotation.is_deleted == False)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_annotations(db: AsyncSession, offset: int = 0, limit: int = 10, keyword: str = None) -> tuple[List[Annotation], int]:
    conditions = [Annotation.is_deleted == False]
    if keyword:
        conditions.append(Annotation.name.ilike(f"%{keyword}%"))
    
    count_stmt = select(func.count()).select_from(Annotation).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()
    
    stmt = select(Annotation).where(*conditions).order_by(Annotation.created_at.desc()).offset(offset).limit(limit)
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
    stmt = update(Annotation).where(Annotation.id == annotation_id).values(is_deleted=True)
    result = await db.execute(stmt)
    return result.rowcount > 0


async def create_annotation_file(db: AsyncSession, **kwargs) -> AnnotationFile:
    file = AnnotationFile(**kwargs)
    db.add(file)
    await db.flush()
    await db.refresh(file)
    return file


async def get_annotation_file(db: AsyncSession, annotation_id: int, file_name: str) -> Optional[AnnotationFile]:
    stmt = select(AnnotationFile).where(
        AnnotationFile.annotation_id == annotation_id,
        AnnotationFile.file_name == file_name,
        AnnotationFile.is_deleted == False
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_annotation_files(db: AsyncSession, annotation_id: int, offset: int = 0, limit: int = 100) -> tuple[List[AnnotationFile], int]:
    conditions = [AnnotationFile.annotation_id == annotation_id, AnnotationFile.is_deleted == False]
    count_stmt = select(func.count()).select_from(AnnotationFile).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()
    
    stmt = select(AnnotationFile).where(*conditions).order_by(AnnotationFile.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def update_annotation_file(db: AsyncSession, file_id: int, content: str) -> Optional[AnnotationFile]:
    stmt = select(AnnotationFile).where(AnnotationFile.id == file_id)
    result = await db.execute(stmt)
    file = result.scalar_one_or_none()
    if file:
        file.content = content
        await db.flush()
        await db.refresh(file)
    return file
