"""标注服务"""
import asyncio
import json
import mimetypes
from datetime import datetime
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
    is_dpo_annotation_type,
    is_dpo_dataset_scenario,
)
from app.common.exceptions import NotFoundException, BadRequestException
from app.config.settings import get_settings
from app.db.models import SampleItem
from app.modules.ai_pipeline.service import AiPipelineService
from app.modules.dataset import crud as dataset_crud
from app.mq.rpc_client import get_assist_rpc_client
from app.utils.annotation_classes import parse_annotation_classes, serialize_annotation_classes
from app.utils.annotation_record_storage import (
    build_annotation_record_object_key,
    is_annotation_record_storage_path,
    parse_annotation_record_payload,
    serialize_annotation_record_payload,
)
from app.utils.s3_delegate import get_s3_delegate
from . import crud
from .schemas import (
    AnnotationAssistRequest,
    AnnotationAssistPipelineResponse,
    AnnotationAssistResponse,
    AnnotationCreate,
    AnnotationExportItem,
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
        self.ai_pipeline_service = AiPipelineService()

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
            default_ai_pipeline_binding_id=data.default_ai_pipeline_binding_id,
            dataset_id=data.dataset_id,
        )
        await self._persist_annotation_project(ann)
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
        await self._persist_annotation_project(ann)
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

        items = await self.list_platform_assist_pipelines(db)
        normalized_shape = (shape or "").strip().lower()
        filtered_items: list[AnnotationAssistPipelineResponse] = []
        for item in items:
            if item.supported_annotation_types and ann.annotation_type not in item.supported_annotation_types:
                continue
            if normalized_shape and item.supported_shapes and normalized_shape not in item.supported_shapes:
                continue
            filtered_items.append(item)
        return filtered_items

    async def list_platform_assist_pipelines(
        self,
        db: AsyncSession,
    ) -> list[AnnotationAssistPipelineResponse]:
        raw_items = await self._load_platform_pipeline_catalog(db)
        items: list[AnnotationAssistPipelineResponse] = []
        for item in raw_items:
            parsed = self._parse_pipeline_descriptor(item)
            if parsed is None:
                continue
            items.append(parsed)
        return items

    async def list_platform_assist_pipeline_details(
        self,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        raw_items = await self._load_platform_pipeline_catalog(db)
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

    async def _load_platform_pipeline_catalog(
        self,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        try:
            db_items = await self.ai_pipeline_service.list_assist_template_detail_descriptors(db)
        except Exception as exc:
            logger.warning(f"Failed to load assist pipelines from DB, fallback to MQ: {exc}")
            db_items = []

        if db_items:
            return db_items

        payload = await self._fetch_pipeline_catalog()
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            pipelines = payload.get("pipelines", [])
            return pipelines if isinstance(pipelines, list) else []
        return []

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
        items = await asyncio.gather(
            *(self._build_annotation_record_response(record) for record in records)
        ) if records else []
        return items, total

    async def list_annotation_records_by_sample_ids(
        self,
        db: AsyncSession,
        annotation_id: int,
        sample_item_ids: list[int],
    ) -> list[AnnotationRecordResponse]:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        normalized_ids = [item for item in dict.fromkeys(sample_item_ids) if item > 0]
        if not normalized_ids:
            return []
        records = await crud.get_annotation_records_by_sample_ids(db, annotation_id, normalized_ids)
        items = await asyncio.gather(
            *(self._build_annotation_record_response(record) for record in records)
        ) if records else []
        return items

    async def export_dpo_records(
        self,
        db: AsyncSession,
        annotation_id: int,
    ) -> tuple[list[AnnotationExportItem], str]:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        if not is_dpo_annotation_type(ann.annotation_type):
            raise BadRequestException("only DPO annotation project supports export")
        if not ann.dataset_id:
            raise BadRequestException("annotation project has no dataset")

        exported_items: list[AnnotationExportItem] = []
        offset = 0
        page_size = 500
        while True:
            records, _ = await crud.get_annotation_records(db, annotation_id, offset, page_size)
            if not records:
                break
            for record in records:
                content = await self._load_annotation_record_content(record.annotation_type, record.content)
                if not isinstance(content, dict):
                    continue
                decision = str(content.get("decision") or "").strip().lower()
                if decision not in {"left", "right"}:
                    continue
                if content.get("skip") is True or content.get("tie") is True:
                    continue

                sample_item = await db.scalar(
                    select(SampleItem).where(
                        SampleItem.id == record.sample_item_id,
                        SampleItem.dataset_id == ann.dataset_id,
                        SampleItem.is_deleted == False,
                    )
                )
                if not sample_item:
                    continue
                sample_payload = self._load_dpo_sample_payload(sample_item.payload)
                if not sample_payload:
                    continue
                response_map = {
                    str(item.get("response_id")): str(item.get("content") or "")
                    for item in sample_payload.get("responses", [])
                    if isinstance(item, dict)
                }
                chosen_response_id = str(
                    content.get("selected_response_id")
                    or content.get("chosen_response_id")
                    or ""
                ).strip()
                rejected_response_ids = [
                    str(item).strip()
                    for item in content.get("rejected_response_ids", []) or []
                    if str(item).strip()
                ]
                legacy_rejected_response_id = str(content.get("rejected_response_id") or "").strip()
                if not rejected_response_ids and legacy_rejected_response_id:
                    rejected_response_ids = [legacy_rejected_response_id]
                chosen = response_map.get(chosen_response_id)
                if chosen is None:
                    continue

                for rejected_response_id in rejected_response_ids:
                    rejected = response_map.get(rejected_response_id)
                    if rejected is None or rejected_response_id == chosen_response_id:
                        continue
                    exported_items.append(
                        AnnotationExportItem(
                            prompt=sample_payload.get("prompt") or {},
                            chosen=chosen,
                            rejected=rejected,
                            chosen_response_id=chosen_response_id,
                            rejected_response_id=rejected_response_id,
                            sample_item_id=sample_item.id,
                            annotation_id=annotation_id,
                            reason=str(content.get("reason") or "").strip() or None,
                        )
                    )
            if len(records) < page_size:
                break
            offset += page_size
        return exported_items, self._build_dpo_export_name(ann.annotation_type)

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
        if not ann.save_path:
            raise BadRequestException("annotation project save_path is empty")

        object_key = build_annotation_record_object_key(
            ann.save_path,
            data.sample_item_id,
            ann.annotation_type,
        )
        existing = await crud.get_annotation_record(db, annotation_id, data.sample_item_id)
        if existing:
            record = await crud.update_annotation_record(
                db,
                existing.id,
                content=object_key,
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
                content=object_key,
            )
        await self._persist_annotation_record(ann, record, data.content)
        return self._to_annotation_record_response(
            record,
            parse_annotation_record_payload(
                ann.annotation_type,
                data.content,
                source_path=object_key,
            ),
        )

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
        resolved_pipeline = await self._resolve_assist_pipeline(
            db,
            ann,
            shape,
            data.pipeline_id,
            requested_binding_id=data.binding_id,
        )
        pipeline = resolved_pipeline["pipeline"]
        binding_context = resolved_pipeline.get("binding_context")
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
        request_params = data.params or {}
        merged_params = self._merge_assist_runtime_params(
            ann=ann,
            request_params=request_params,
            binding_context=binding_context,
            selected_classes=selected_classes,
        )

        request_payload = {
            "input": {
                "image": {
                    "base64_data": image_base64,
                    "mime_type": mime_type,
                },
                "classes": selected_classes,
                "prompt": self._resolve_assist_prompt(ann, merged_params),
                "metadata": {
                    "annotation_id": annotation_id,
                    "dataset_id": ann.dataset_id,
                    "sample_item_id": sample_item.id,
                    "item_key": sample_item.item_key,
                    "file_name": file_name,
                    "shape": shape,
                    "pipeline_id": pipeline.id,
                    "binding_id": binding_context.get("binding_id") if binding_context else None,
                },
            },
            "params": merged_params,
        }
        logger.info(
            "Assist annotation request annotation_id=%s file=%s pipeline=%s binding_id=%s shape=%s classes=%s prompt=%s",
            annotation_id,
            file_name,
            pipeline.id,
            binding_context.get("binding_id") if binding_context else None,
            shape,
            selected_classes,
            request_payload["input"]["prompt"],
        )
        try:
            rpc_payload = {
                "action": "run_pipeline",
                "pipeline_name": pipeline.id,
                "request": request_payload,
            }
            if binding_context:
                definition_json = binding_context.get("definition_json")
                if isinstance(definition_json, dict):
                    rpc_payload["definition"] = definition_json
            payload = await asyncio.to_thread(
                self.assist_rpc_client.call,
                rpc_payload,
                get_settings().ai_pipeline_runtime.timeout,
            )
        except Exception as exc:
            logger.error(f"Failed to call ai_pipeline_runtime by MQ: {exc}")
            raise BadRequestException(f"ai_pipeline_runtime unavailable: {exc}")

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
                get_settings().ai_pipeline_runtime.timeout,
            )
        except Exception as exc:
            logger.error(f"Failed to list ai_pipeline_runtime pipelines by MQ: {exc}")
            raise BadRequestException(f"ai_pipeline_runtime unavailable: {exc}")

    async def _resolve_assist_pipeline(
        self,
        db: AsyncSession,
        ann,
        shape: str,
        requested_pipeline_id: Optional[str],
        requested_binding_id: Optional[int] = None,
    ) -> dict[str, Any]:
        pipelines = await self.list_assist_pipelines(db, ann.id, shape=shape)
        if not pipelines:
            raise BadRequestException(f"no annotation assist pipeline supports shape `{shape}`")

        binding_context = await self._load_annotation_binding_context(
            db,
            ann,
            requested_binding_id=requested_binding_id,
        )
        if requested_binding_id and not binding_context:
            raise BadRequestException(
                f"ai pipeline binding `{requested_binding_id}` not available for current annotation"
            )
        binding_pipeline_id = None
        if binding_context:
            binding_descriptor = binding_context.get("pipeline_descriptor") or {}
            binding_pipeline_id = str(
                binding_descriptor.get("name")
                or binding_descriptor.get("id")
                or ""
            ).strip() or None

        pipeline_id = requested_pipeline_id or binding_pipeline_id or getattr(ann, "assist_pipeline", None)
        if pipeline_id:
            matched = next((item for item in pipelines if item.id == pipeline_id), None)
            if matched:
                if getattr(ann, "assist_pipeline", None) != matched.id:
                    await crud.update_annotation(db, ann.id, assist_pipeline=matched.id)
                return {
                    "pipeline": matched,
                    "binding_context": binding_context if binding_pipeline_id == matched.id else None,
                }
            raise BadRequestException(f"annotation assist pipeline `{pipeline_id}` does not support current annotation shape")

        selected = pipelines[0]
        await crud.update_annotation(db, ann.id, assist_pipeline=selected.id)
        return {
            "pipeline": selected,
            "binding_context": binding_context if binding_pipeline_id == selected.id else None,
        }

    async def _load_annotation_binding_context(
        self,
        db: AsyncSession,
        ann,
        requested_binding_id: Optional[int] = None,
    ) -> dict[str, Any] | None:
        binding_id = requested_binding_id or getattr(ann, "default_ai_pipeline_binding_id", None)
        if not binding_id:
            return None
        try:
            binding_context = await self.ai_pipeline_service.get_binding_execution_context(
                db,
                binding_id,
            )
        except Exception as exc:
            logger.warning(
                f"Failed to load annotation default AI pipeline binding {binding_id}: {exc}"
            )
            return None
        if not binding_context:
            return None
        if binding_context.get("binding_type") != "annotation_project":
            logger.warning(
                "Ignore AI pipeline binding %s for annotation %s due to binding_type=%s",
                binding_id,
                ann.id,
                binding_context.get("binding_type"),
            )
            return None
        if int(binding_context.get("binding_target_id") or 0) != int(ann.id):
            logger.warning(
                "Ignore AI pipeline binding %s for annotation %s due to binding_target_id=%s",
                binding_id,
                ann.id,
                binding_context.get("binding_target_id"),
            )
            return None
        return binding_context

    def _merge_assist_runtime_params(
        self,
        *,
        ann,
        request_params: dict[str, Any],
        binding_context: dict[str, Any] | None,
        selected_classes: list[str],
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        if binding_context:
            runtime_defaults = binding_context.get("runtime_input_defaults_json")
            if isinstance(runtime_defaults, dict):
                merged.update(runtime_defaults)

            resource_bindings = binding_context.get("resource_bindings_json")
            if resource_bindings is not None:
                merged["resource_bindings"] = resource_bindings
                merged["ai_pipeline_resource_bindings"] = resource_bindings

            merged["ai_pipeline_binding_id"] = binding_context.get("binding_id")
            merged["ai_pipeline_template_key"] = binding_context.get("template_key")
            merged["ai_pipeline_template_version"] = binding_context.get("template_version")

        merged.update(request_params)
        merged["classes"] = selected_classes
        if ann.prompt and "prompt" not in merged:
            merged["prompt"] = ann.prompt
        return merged

    def _resolve_assist_prompt(
        self,
        ann,
        request_params: dict[str, Any],
    ) -> str | None:
        prompt = request_params.get("prompt")
        if prompt is None:
            prompt = request_params.get("user_prompt")
        if prompt is None:
            return ann.prompt
        prompt_text = str(prompt).strip()
        return prompt_text or ann.prompt

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

    async def _build_annotation_record_response(self, record) -> AnnotationRecordResponse:
        content = await self._load_annotation_record_content(record.annotation_type, record.content)
        return self._to_annotation_record_response(record, content)

    async def _load_annotation_record_content(
        self,
        annotation_type: int,
        content_path: Any,
    ) -> dict[str, Any] | None:
        if not is_annotation_record_storage_path(content_path):
            return None
        try:
            payload = await self.s3.get_file(content_path, bucket_type="annotations")
        except Exception as e:
            logger.warning(f"Failed to load annotation record content from {content_path}: {e}")
            return None
        return parse_annotation_record_payload(
            annotation_type,
            payload,
            source_path=content_path,
        )

    def _to_annotation_record_response(
        self,
        record,
        content: dict[str, Any] | None = None,
    ) -> AnnotationRecordResponse:
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

    async def _persist_annotation_project(self, ann) -> None:
        if not ann.save_path:
            return
        payload = {
            "id": ann.id,
            "name": ann.name,
            "annotation_type": ann.annotation_type,
            "classes": parse_annotation_classes(ann.classes),
            "storage_type": ann.storage_type,
            "dataset_id": ann.dataset_id,
            "prompt": ann.prompt,
            "assist_pipeline": ann.assist_pipeline,
            "default_ai_pipeline_binding_id": getattr(ann, "default_ai_pipeline_binding_id", None),
            "created_at": self._json_time(ann.created_at),
            "updated_at": self._json_time(ann.updated_at),
        }
        await self.s3.put_file(
            f"{ann.save_path}/project.json",
            json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            bucket_type="annotations",
            content_type="application/json",
        )

    async def _persist_annotation_record(
        self,
        ann,
        record,
        content: dict[str, Any],
    ) -> None:
        if not ann.save_path or not record.content:
            return
        payload_bytes, content_type = serialize_annotation_record_payload(
            record.annotation_type,
            content,
        )
        await self.s3.put_file(
            record.content,
            payload_bytes,
            bucket_type="annotations",
            content_type=content_type,
        )

    def _json_time(self, value: Any) -> str | None:
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value) if value is not None else None

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
            raise BadRequestException("annotation project requires dataset_id")

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
        if annotation_type == AnnotationType.DPO and (
            dataset.data_type != DataType.TEXT or not is_dpo_dataset_scenario(dataset.scenario_type)
        ):
            raise BadRequestException("DPO annotation project can only bind DPO datasets")
        if annotation_type == AnnotationType.DPO_PAIRWISE and (
            dataset.data_type != DataType.TEXT or dataset.scenario_type != DatasetScenarioType.DPO_PAIRWISE
        ):
            raise BadRequestException("DPO pairwise annotation project can only bind DPO pairwise datasets")
        if annotation_type == AnnotationType.DPO_BEST_OF_N and (
            dataset.data_type != DataType.TEXT or dataset.scenario_type != DatasetScenarioType.DPO_BEST_OF_N
        ):
            raise BadRequestException("DPO best_of_n annotation project can only bind DPO best_of_n datasets")
        if annotation_type == AnnotationType.DPO_REFERENCE_CHOICE and (
            dataset.data_type != DataType.TEXT or dataset.scenario_type != DatasetScenarioType.DPO_REFERENCE_CHOICE
        ):
            raise BadRequestException("DPO reference choice annotation project can only bind DPO reference choice datasets")
        if annotation_type == AnnotationType.DPO_MULTI_TURN and (
            dataset.data_type != DataType.TEXT or dataset.scenario_type != DatasetScenarioType.DPO_MULTI_TURN
        ):
            raise BadRequestException("DPO multi_turn annotation project can only bind DPO multi_turn datasets")

    def _load_dpo_sample_payload(self, raw_payload: Any) -> dict[str, Any] | None:
        if not raw_payload:
            return None
        if isinstance(raw_payload, dict):
            return raw_payload
        try:
            parsed = json.loads(raw_payload)
        except (TypeError, json.JSONDecodeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    def _build_dpo_export_name(self, annotation_type: int) -> str:
        if annotation_type == AnnotationType.DPO_PAIRWISE:
            return "dpo_pairwise_annotation"
        if annotation_type == AnnotationType.DPO_BEST_OF_N:
            return "dpo_best_of_n_annotation"
        if annotation_type == AnnotationType.DPO_REFERENCE_CHOICE:
            return "dpo_reference_annotation"
        if annotation_type == AnnotationType.DPO_MULTI_TURN:
            return "dpo_multi_turn_annotation"
        return "dpo_annotation"


async def get_annotation_service():
    service = AnnotationService()
    try:
        yield service
    finally:
        await service.close()
