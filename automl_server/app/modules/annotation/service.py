"""标注服务"""
import asyncio
import json
import mimetypes
from typing import Any
import uuid
from typing import List, Optional
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.constants import (
    AnnotationType,
    DataType,
    DatasetScenarioType,
    get_annotation_type_definition,
    get_annotation_type_definitions,
)
from app.common.exceptions import NotFoundException, BadRequestException
from app.config.settings import get_settings
from app.db.models import SampleItem
from app.modules.dataset import crud as dataset_crud
from app.mq.rpc_client import get_assist_rpc_client
from app.utils.annotation_classes import parse_annotation_classes, serialize_annotation_classes
from app.utils.s3_delegate import get_s3_delegate
from . import crud
from .schemas import (
    AnnotationAssistRequest,
    AnnotationAssistPipelineResponse,
    AnnotationAssistResponse,
    AnnotationCreate,
    AnnotationRecordResponse,
    AnnotationRecordSave,
    AnnotationTypeDefinitionResponse,
    AnnotationUpdate,
    AnnotationResponse,
)


class AnnotationService:
    def __init__(self):
        self.s3 = get_s3_delegate()
        self._assist_rpc_client = None

    async def close(self):
        return None

    @property
    def assist_rpc_client(self):
        if self._assist_rpc_client is None:
            self._assist_rpc_client = get_assist_rpc_client()
        return self._assist_rpc_client

    def list_annotation_types(self) -> list[AnnotationTypeDefinitionResponse]:
        return [
            AnnotationTypeDefinitionResponse(**definition.__dict__)
            for definition in get_annotation_type_definitions()
        ]

    async def create_annotation(self, db: AsyncSession, data: AnnotationCreate) -> AnnotationResponse:
        await self._validate_annotation_dataset_link(db, data.annotation_type, data.dataset_id)
        type_definition = get_annotation_type_definition(data.annotation_type)

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
            classes=serialize_annotation_classes(data.classes) if type_definition and type_definition.supports_classes else None,
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
        if "classes" in update_data:
            ann = await crud.get_annotation_by_id(db, annotation_id)
            if not ann:
                raise NotFoundException(f"Annotation {annotation_id} not found")
            type_definition = get_annotation_type_definition(ann.annotation_type)
            update_data["classes"] = (
                serialize_annotation_classes(update_data["classes"])
                if type_definition and type_definition.supports_classes
                else None
            )
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

        items = await self.list_platform_assist_pipelines()
        normalized_shape = (shape or "").strip().lower()
        filtered_items: list[AnnotationAssistPipelineResponse] = []
        for item in items:
            if item.supported_annotation_types and ann.annotation_type not in item.supported_annotation_types:
                continue
            if normalized_shape and item.supported_shapes and normalized_shape not in item.supported_shapes:
                continue
            filtered_items.append(item)
        return filtered_items

    async def list_platform_assist_pipelines(self) -> list[AnnotationAssistPipelineResponse]:
        payload = await self._fetch_pipeline_catalog()
        if isinstance(payload, list):
            raw_items = payload
        elif isinstance(payload, dict):
            raw_items = payload.get("pipelines", [])
        else:
            raw_items = []

        items: list[AnnotationAssistPipelineResponse] = []
        for item in raw_items:
            parsed = self._parse_pipeline_descriptor(item)
            if parsed is None:
                continue
            items.append(parsed)
        return items

    async def list_platform_assist_pipeline_details(self) -> list[dict[str, Any]]:
        payload = await self._fetch_pipeline_catalog()
        if isinstance(payload, list):
            raw_items = payload
        elif isinstance(payload, dict):
            raw_items = payload.get("pipelines", [])
        else:
            raw_items = []

        items: list[dict[str, Any]] = []
        for item in raw_items:
            parsed = self._parse_pipeline_descriptor(item)
            if parsed is None:
                continue
            items.append({
                **parsed.model_dump(mode="json"),
                "steps": self._parse_pipeline_steps(item),
            })
        return items

    async def list_annotation_records(
        self,
        db: AsyncSession,
        annotation_id: int,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[AnnotationRecordResponse], int]:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        offset = (page - 1) * page_size
        records, total = await crud.get_annotation_records(db, annotation_id, offset, page_size)
        return [self._to_annotation_record_response(record) for record in records], total

    async def save_annotation_record(
        self,
        db: AsyncSession,
        annotation_id: int,
        data: AnnotationRecordSave,
    ) -> AnnotationRecordResponse:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        sample_item = await db.scalar(
            select(SampleItem).where(
                SampleItem.id == data.sample_item_id,
                SampleItem.is_deleted == False,
            )
        )
        if not sample_item:
            raise NotFoundException(f"Sample item {data.sample_item_id} not found")
        if ann.dataset_id and sample_item.dataset_id != ann.dataset_id:
            raise BadRequestException("sample item does not belong to annotation dataset")

        content = json.dumps(data.content, ensure_ascii=False)
        existing = await crud.get_annotation_record(db, annotation_id, data.sample_item_id)
        if existing:
            record = await crud.update_annotation_record(
                db,
                existing.id,
                content=content,
                status=data.status,
                annotation_type=ann.annotation_type,
            )
        else:
            record = await crud.create_annotation_record(
                db,
                annotation_id=annotation_id,
                sample_item_id=data.sample_item_id,
                annotation_type=ann.annotation_type,
                status=data.status,
                content=content,
            )
        return self._to_annotation_record_response(record)

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

        classes = parse_annotation_classes(ann.classes)
        if not classes:
            raise BadRequestException("annotation assist requires non-empty classes")
        selected_classes = self._normalize_target_classes(data.target_classes, classes)
        shape = (data.shape or "bbox").strip().lower()
        pipeline = await self._resolve_assist_pipeline(db, ann, shape, data.pipeline_id)
        if shape != "bbox":
            raise BadRequestException("selected annotation assist pipeline currently only returns bbox annotations")

        sample_item = await db.scalar(
            select(SampleItem).where(
                SampleItem.id == data.sample_item_id,
                SampleItem.dataset_id == ann.dataset_id,
                SampleItem.is_deleted == False,
            )
        )
        if not sample_item:
            raise NotFoundException(f"Sample item {data.sample_item_id} not found")
        if not sample_item.asset_id:
            raise BadRequestException("annotation assist requires an asset-backed sample")
        asset = await dataset_crud.get_asset_by_id(db, sample_item.asset_id)
        if not asset or not asset.save_path:
            raise NotFoundException(f"Asset for sample {data.sample_item_id} not found")

        image_bytes = await self.s3.get_file(asset.save_path, bucket_type="datasets")
        file_name = asset.file_name or sample_item.item_key
        mime_type = asset.mime_type or mimetypes.guess_type(file_name)[0] or "image/jpeg"
        image_base64 = self._to_data_url(image_bytes, mime_type)

        request_payload = {
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
                    "sample_item_id": sample_item.id,
                    "item_key": sample_item.item_key,
                    "file_name": file_name,
                    "shape": shape,
                    "pipeline_id": pipeline.id,
                },
            },
            "params": data.params or {},
        }
        logger.info(
            "Assist annotation request annotation_id=%s file=%s pipeline=%s shape=%s classes=%s prompt=%s",
            annotation_id,
            file_name,
            pipeline.id,
            shape,
            selected_classes,
            ann.prompt,
        )
        try:
            payload = await asyncio.to_thread(
                self.assist_rpc_client.call,
                {
                    "action": "run_pipeline",
                    "pipeline_name": pipeline.id,
                    "request": request_payload,
                },
                get_settings().auto_augment_pipeline.timeout,
            )
        except Exception as exc:
            logger.error(f"Failed to call auto_augment_pipeline by MQ: {exc}")
            raise BadRequestException(f"auto_augment_pipeline unavailable: {exc}")

        result = self._extract_pipeline_annotation_result(payload, pipeline.id)
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
            sample_item_id=sample_item.id,
            item_key=sample_item.item_key,
            image_width=int(result.get("image_width", 0) or 0),
            image_height=int(result.get("image_height", 0) or 0),
            annotations=items,
            replace_existing=data.replace_existing,
            debug=result.get("raw") if isinstance(result.get("raw"), dict) else None,
        )

    async def _fetch_pipeline_catalog(self) -> Any:
        try:
            return await asyncio.to_thread(
                self.assist_rpc_client.call,
                {"action": "list_pipelines"},
                get_settings().auto_augment_pipeline.timeout,
            )
        except Exception as exc:
            logger.error(f"Failed to list auto_augment_pipeline pipelines by MQ: {exc}")
            raise BadRequestException(f"auto_augment_pipeline unavailable: {exc}")

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
            enabled=bool(item.get("enabled", True)),
        )

    def _looks_like_assist_pipeline(self, item: dict[str, Any]) -> bool:
        assist_capabilities = {
            "assist_annotation",
            "draft_annotation",
            "draft_annotation_preview",
            "extract_white_annotations",
            "render_white_annotation_overlay",
            "understand_white_annotations",
        }
        for step in item.get("steps", []) or []:
            if isinstance(step, dict) and step.get("capability") in assist_capabilities:
                return True
        return False

    def _parse_pipeline_steps(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        steps: list[dict[str, Any]] = []
        for step in item.get("steps", []) or []:
            if not isinstance(step, dict):
                continue
            capability = str(step.get("capability") or "").strip()
            name = str(step.get("name") or capability or "step").strip()
            provider = str(step.get("provider") or "").strip() or None
            if not capability and not name:
                continue
            steps.append({
                "name": name,
                "capability": capability or name,
                "provider": provider,
            })
        return steps

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

    def _to_annotation_record_response(self, record) -> AnnotationRecordResponse:
        content = None
        if record.content:
            try:
                parsed = json.loads(record.content)
                if isinstance(parsed, dict):
                    content = parsed
            except json.JSONDecodeError:
                content = None
        return AnnotationRecordResponse(
            id=record.id,
            annotation_id=record.annotation_id,
            sample_item_id=record.sample_item_id,
            annotation_type=record.annotation_type,
            status=record.status,
            content=content,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _to_data_url(self, data: bytes, mime_type: str) -> str:
        import base64
        encoded = base64.b64encode(data).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    async def _validate_annotation_dataset_link(
        self,
        db: AsyncSession,
        annotation_type: int,
        dataset_id: Optional[int],
    ) -> None:
        if get_annotation_type_definition(annotation_type) is None:
            raise BadRequestException(f"unsupported annotation type: {annotation_type}")

        if dataset_id is None:
            return

        dataset = await dataset_crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")

        if annotation_type == AnnotationType.LLM and (
            dataset.data_type != DataType.TEXT or dataset.scenario_type != DatasetScenarioType.LLM_CONVERSATION
        ):
            raise BadRequestException("LLM annotation project can only bind LLM conversation datasets")
        if annotation_type == AnnotationType.MLLM and (
            dataset.data_type != DataType.IMAGE or dataset.scenario_type != DatasetScenarioType.MLLM_CONVERSATION
        ):
            raise BadRequestException("MLLM annotation project can only bind MLLM conversation datasets")


async def get_annotation_service():
    service = AnnotationService()
    try:
        yield service
    finally:
        await service.close()
