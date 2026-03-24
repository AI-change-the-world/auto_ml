"""标注服务"""
import uuid
from typing import List, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import NotFoundException
from app.utils.s3_delegate import get_s3_delegate
from . import crud
from .schemas import AnnotationCreate, AnnotationUpdate, AnnotationResponse, AnnotationFileSave


class AnnotationService:
    def __init__(self):
        self.s3 = get_s3_delegate()
    
    async def create_annotation(self, db: AsyncSession, data: AnnotationCreate) -> AnnotationResponse:
        ann_uuid = str(uuid.uuid4())
        save_path = f"annotations/{ann_uuid}"
        
        try:
            await self.s3.create_directory(save_path, bucket_type="annotations")
        except Exception as e:
            logger.error(f"Failed to create annotation directory: {e}")
        
        ann = await crud.create_annotation(
            db,
            name=data.name,
            annotation_type=data.annotation_type,
            classes=data.classes,
            storage_type=data.storage_type,
            save_path=save_path,
            prompt=data.prompt,
            dataset_id=data.dataset_id,
        )
        logger.info(f"Annotation created: {ann.name}")
        return AnnotationResponse.model_validate(ann)
    
    async def get_annotation(self, db: AsyncSession, annotation_id: int) -> AnnotationResponse:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        return AnnotationResponse.model_validate(ann)
    
    async def list_annotations(self, db: AsyncSession, page: int = 1, page_size: int = 10, keyword: str = None) -> tuple[List[AnnotationResponse], int]:
        offset = (page - 1) * page_size
        items, total = await crud.get_annotations(db, offset, page_size, keyword)
        return [AnnotationResponse.model_validate(item) for item in items], total
    
    async def update_annotation(self, db: AsyncSession, annotation_id: int, data: AnnotationUpdate) -> AnnotationResponse:
        update_data = data.model_dump(exclude_unset=True)
        ann = await crud.update_annotation(db, annotation_id, **update_data)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        return AnnotationResponse.model_validate(ann)
    
    async def delete_annotation(self, db: AsyncSession, annotation_id: int) -> bool:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        return await crud.delete_annotation(db, annotation_id)
    
    async def save_annotation_file(self, db: AsyncSession, annotation_id: int, data: AnnotationFileSave) -> int:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        
        # 上传到 S3
        file_key = f"{ann.save_path}/{data.file_name}"
        await self.s3.put_file(file_key, data.content.encode(), bucket_type="annotations")
        
        # 检查是否已存在
        existing = await crud.get_annotation_file(db, annotation_id, data.file_name)
        if existing:
            await crud.update_annotation_file(db, existing.id, data.content)
            return existing.id
        else:
            file = await crud.create_annotation_file(
                db,
                annotation_id=annotation_id,
                file_name=data.file_name,
                save_path=file_key,
                content=data.content,
            )
            return file.id
    
    async def get_files(self, db: AsyncSession, annotation_id: int, page: int = 1, page_size: int = 100) -> tuple[list, int]:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        offset = (page - 1) * page_size
        return await crud.get_annotation_files(db, annotation_id, offset, page_size)


_service: Optional[AnnotationService] = None

def get_annotation_service() -> AnnotationService:
    global _service
    if _service is None:
        _service = AnnotationService()
    return _service
