"""标注服务"""
import json
import mimetypes
from typing import Any
import uuid
from typing import List, Optional
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import NotFoundException, BadRequestException
from app.config.settings import get_settings
from app.db.models import DatasetFile
from app.utils.s3_delegate import get_s3_delegate
from app.utils.http_client import HttpClient
from . import crud
from .schemas import (
    AnnotationAssistRequest,
    AnnotationAssistResponse,
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationResponse,
    AnnotationFileSave,
)


class AnnotationService:
    def __init__(self):
        self.s3 = get_s3_delegate()
        self._augment_client = None

    @property
    def augment_client(self) -> HttpClient:
        if self._augment_client is None:
            settings = get_settings()
            self._augment_client = HttpClient(
                base_url=settings.auto_augment_pipeline.base_url,
                timeout=settings.auto_augment_pipeline.timeout,
            )
        return self._augment_client

    async def close(self):
        if self._augment_client is not None:
            await self._augment_client.close()
            self._augment_client = None

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

    async def assist_current_file(
        self,
        db: AsyncSession,
        annotation_id: int,
        data: AnnotationAssistRequest,
    ) -> AnnotationAssistResponse:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        if ann.annotation_type != 0:
            raise BadRequestException("annotation assist currently only supports detection projects")
        if not ann.dataset_id or not ann.classes:
            raise BadRequestException("annotation assist requires dataset_id and non-empty classes")

        classes = self._parse_classes(ann.classes)
        if not classes:
            raise BadRequestException("annotation assist requires non-empty classes")

        dataset_file = await db.scalar(
            select(DatasetFile).where(
                DatasetFile.dataset_id == ann.dataset_id,
                DatasetFile.file_name == data.file_name,
                DatasetFile.is_deleted == False,
            )
        )
        if not dataset_file or not dataset_file.save_path:
            raise NotFoundException(f"Dataset file {data.file_name} not found")

        image_bytes = await self.s3.get_file(dataset_file.save_path, bucket_type="datasets")
        mime_type = mimetypes.guess_type(data.file_name)[0] or "image/jpeg"
        image_base64 = self._to_data_url(image_bytes, mime_type)

        settings = get_settings()
        profile = data.profile or settings.auto_augment_pipeline.default_profile
        request_payload = {
            "profile": profile,
            "input": {
                "image": {
                    "base64_data": image_base64,
                    "mime_type": mime_type,
                },
                "classes": classes,
                "prompt": ann.prompt,
                "metadata": {
                    "annotation_id": annotation_id,
                    "dataset_id": ann.dataset_id,
                    "file_name": data.file_name,
                },
            },
            "params": {},
        }

        try:
            response = await self.augment_client.post(
                "/v1/capabilities/assist_annotation/run",
                json=request_payload,
            )
        except Exception as exc:
            logger.error(f"Failed to call auto_augment_pipeline: {exc}")
            raise BadRequestException(f"auto_augment_pipeline unavailable: {exc}")

        if response.status_code != 200:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                pass
            raise BadRequestException(f"annotation assist failed: {detail}")

        result = response.json()
        raw_annotations = result.get("annotations", [])
        items = []
        for item in raw_annotations:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "")).strip()
            bbox = item.get("bbox") or {}
            if not label or not {"x1", "y1", "x2", "y2"} <= set(bbox.keys()):
                continue
            items.append(
                {
                    "label": label,
                    "bbox": {
                        "x1": int(bbox["x1"]),
                        "y1": int(bbox["y1"]),
                        "x2": int(bbox["x2"]),
                        "y2": int(bbox["y2"]),
                    },
                    "confidence": item.get("confidence"),
                    "source": item.get("source"),
                }
            )

        return AnnotationAssistResponse(
            file_name=data.file_name,
            image_width=int(result.get("image_width", 0) or 0),
            image_height=int(result.get("image_height", 0) or 0),
            annotations=items,
            profile=profile,
            replace_existing=data.replace_existing,
            debug=result.get("raw") if isinstance(result.get("raw"), dict) else None,
        )

    def _parse_classes(self, raw_classes: Optional[str]) -> List[str]:
        if not raw_classes:
            return []
        try:
            parsed = json.loads(raw_classes)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
        return [item.strip() for item in raw_classes.split(",") if item.strip()]

    def _to_data_url(self, data: bytes, mime_type: str) -> str:
        import base64
        encoded = base64.b64encode(data).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"


async def get_annotation_service():
    service = AnnotationService()
    try:
        yield service
    finally:
        await service.close()
