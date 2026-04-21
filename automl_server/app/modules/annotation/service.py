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
    AnnotationAssistPipelineResponse,
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
            assist_pipeline=data.assist_pipeline,
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

    async def list_assist_pipelines(
        self,
        db: AsyncSession,
        annotation_id: int,
        shape: Optional[str] = None,
    ) -> list[AnnotationAssistPipelineResponse]:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")

        payload = await self._fetch_pipeline_catalog()
        raw_items = payload.get("pipelines", payload if isinstance(payload, list) else [])
        items: list[AnnotationAssistPipelineResponse] = []
        normalized_shape = (shape or "").strip().lower()
        for item in raw_items:
            parsed = self._parse_pipeline_descriptor(item)
            if parsed is None:
                continue
            if parsed.supported_annotation_types and ann.annotation_type not in parsed.supported_annotation_types:
                continue
            if normalized_shape and parsed.supported_shapes and normalized_shape not in parsed.supported_shapes:
                continue
            items.append(parsed)
        return items

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
        selected_classes = self._normalize_target_classes(data.target_classes, classes)
        shape = (data.shape or "bbox").strip().lower()
        pipeline = await self._resolve_assist_pipeline(db, ann, shape, data.pipeline_id)
        if shape != "bbox":
            raise BadRequestException("selected annotation assist pipeline currently only returns bbox annotations")

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
        profile = data.profile or pipeline.default_profile or settings.auto_augment_pipeline.default_profile
        request_payload = {
            "profile": profile,
            "input": {
                "image": {
                    "base64_data": image_base64,
                    "mime_type": mime_type,
                },
                "classes": selected_classes,
                "prompt": ann.prompt,
                "metadata": {
                    "annotation_id": annotation_id,
                    "dataset_id": ann.dataset_id,
                    "file_name": data.file_name,
                    "shape": shape,
                    "pipeline_id": pipeline.id,
                },
            },
            "params": data.params or {},
        }
        if data.profile:
            request_payload["provider_overrides"] = {}

        try:
            response = await self.augment_client.post(
                f"/v1/pipelines/{pipeline.id}/run",
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

        result = self._extract_pipeline_annotation_result(response.json(), pipeline.id)
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

    async def _fetch_pipeline_catalog(self) -> Any:
        try:
            response = await self.augment_client.get("/v1/pipelines")
        except Exception as exc:
            logger.error(f"Failed to list auto_augment_pipeline pipelines: {exc}")
            raise BadRequestException(f"auto_augment_pipeline unavailable: {exc}")
        if response.status_code != 200:
            raise BadRequestException(f"failed to list annotation assist pipelines: {response.text}")
        return response.json()

    async def _resolve_assist_pipeline(
        self,
        db: AsyncSession,
        ann,
        shape: str,
        requested_pipeline_id: Optional[str],
    ) -> AnnotationAssistPipelineResponse:
        pipelines = await self.list_assist_pipelines(db, ann.id, shape=shape)
        if not pipelines:
            raise BadRequestException(f"no annotation assist pipeline supports shape `{shape}`")

        pipeline_id = requested_pipeline_id or getattr(ann, "assist_pipeline", None)
        if pipeline_id:
            matched = next((item for item in pipelines if item.id == pipeline_id), None)
            if matched:
                if getattr(ann, "assist_pipeline", None) != matched.id:
                    await crud.update_annotation(db, ann.id, assist_pipeline=matched.id)
                return matched
            raise BadRequestException(f"annotation assist pipeline `{pipeline_id}` does not support current annotation shape")

        selected = pipelines[0]
        await crud.update_annotation(db, ann.id, assist_pipeline=selected.id)
        return selected

    def _parse_pipeline_descriptor(self, item: Any) -> AnnotationAssistPipelineResponse | None:
        if not isinstance(item, dict):
            return None
        pipeline_type = str(item.get("pipeline_type") or "").strip()
        inferred_assist = self._looks_like_assist_pipeline(item)
        if not pipeline_type and inferred_assist:
            pipeline_type = "assist_annotation"
        if not pipeline_type:
            pipeline_type = "generic"
        if pipeline_type != "assist_annotation":
            return None
        if item.get("enabled") is False:
            return None
        pipeline_id = str(item.get("name") or item.get("id") or "").strip()
        if not pipeline_id:
            return None
        supported_annotation_types = [
            int(value) for value in item.get("supported_annotation_types", []) or []
            if str(value).strip().lstrip("-").isdigit()
        ]
        supported_shapes = [
            str(value).strip().lower() for value in item.get("supported_shapes", []) or []
            if str(value).strip()
        ]
        if inferred_assist and not supported_annotation_types:
            supported_annotation_types = [0]
        if inferred_assist and not supported_shapes:
            supported_shapes = ["bbox"]
        return AnnotationAssistPipelineResponse(
            id=pipeline_id,
            name=str(item.get("display_name") or pipeline_id),
            description=item.get("description"),
            supported_annotation_types=supported_annotation_types,
            supported_shapes=supported_shapes,
            default_profile=item.get("default_profile"),
            enabled=bool(item.get("enabled", True)),
        )

    def _looks_like_assist_pipeline(self, item: dict[str, Any]) -> bool:
        assist_capabilities = {
            "assist_annotation",
            "draft_annotation",
            "extract_white_annotations",
            "render_white_annotation_overlay",
            "understand_white_annotations",
        }
        for step in item.get("steps", []) or []:
            if isinstance(step, dict) and step.get("capability") in assist_capabilities:
                return True
        return False

    def _normalize_target_classes(
        self,
        requested: Optional[list[str]],
        allowed_classes: list[str],
    ) -> list[str]:
        if not requested:
            return allowed_classes
        allowed = set(allowed_classes)
        selected = [item.strip() for item in requested if item.strip() in allowed]
        if not selected:
            raise BadRequestException("target_classes must be a non-empty subset of annotation classes")
        return selected

    def _extract_pipeline_annotation_result(self, payload: Any, pipeline_id: str) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {"annotations": [], "raw": {"pipeline_payload": payload}}
        if "annotations" in payload:
            return payload

        context = payload.get("context")
        if not isinstance(context, dict):
            return {"annotations": [], "raw": {"pipeline_payload": payload}}

        candidate_keys = [
            "overlay_annotations",
            "draft_annotations",
            "assist_annotations",
            pipeline_id,
        ]
        for key in candidate_keys:
            candidate = context.get(key)
            if isinstance(candidate, dict) and "annotations" in candidate:
                return candidate

        for candidate in reversed(list(context.values())):
            if isinstance(candidate, dict) and "annotations" in candidate:
                return candidate
        return {"annotations": [], "raw": {"pipeline_payload": payload}}

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
