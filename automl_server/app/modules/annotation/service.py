"""标注服务"""
import asyncio
import json
import secrets
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from typing import Any
import uuid
from typing import List, Optional
from loguru import logger
from sqlalchemy import func, select
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
from app.common.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.config.settings import get_settings
from app.db.models import Annotation, AnnotationRecord, AnnotationSampleAssignment, Asset, SampleItem
from app.modules.dataset.schemas import AssetResponse, SampleItemResponse
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
    AnnotationAssistPipelineDetailResponse,
    AnnotationAssistPipelineResponse,
    AnnotationAssistResponse,
    AnnotationCreate,
    AnnotationCollaboratorResponse,
    AnnotationCollaboratorSummaryResponse,
    AnnotationCollaborationClaimRequest,
    AnnotationCollaborationClaimResponse,
    AnnotationCollaborationSamplesResponse,
    AnnotationCollaborationSessionRequest,
    AnnotationCollaborationSessionResponse,
    AnnotationCollaborationStatsResponse,
    AnnotationExportItem,
    AnnotationPresenceHeartbeatRequest,
    AnnotationRecordResponse,
    AnnotationRecordSave,
    AnnotationSampleAssignmentResponse,
    AnnotationSummaryResponse,
    AnnotationTypeDefinitionResponse,
    AnnotationUpdate,
    AnnotationResponse,
)


ANNOTATION_PRESENCE_TTL_SECONDS = 30


@dataclass
class AnnotationPresenceEntry:
    annotation_id: int
    participant_id: str
    display_name: str
    sample_item_id: int | None
    last_active_at: datetime


_annotation_presence: dict[int, dict[str, AnnotationPresenceEntry]] = {}


class AnnotationService:
    COLLABORATION_LEASE_MINUTES = 45

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
        return self._to_annotation_response(ann)

    async def get_annotation(self, db: AsyncSession, annotation_id: int) -> AnnotationResponse:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        collaborators = self._get_presence_summaries(annotation_id)
        return self._to_annotation_response(ann, collaborators)

    async def list_annotations(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        keyword: str = None,
        dataset_id: int | None = None,
    ) -> tuple[List[AnnotationResponse], int]:
        offset = (page - 1) * page_size
        items, total = await crud.get_annotations(db, offset, page_size, keyword, dataset_id)
        collaborator_map = self._get_presence_summary_map([item.id for item in items])
        logger.info(
            "[annotation:presence:list] page={} page_size={} keyword={} total={} collaborators={}",
            page,
            page_size,
            keyword,
            total,
            [
                {
                    "annotation_id": item.id,
                    "name": item.name,
                    "collaborators": [
                        {
                            "participant_id": collaborator.participant_id,
                            "display_name": collaborator.display_name,
                            "sample_item_id": collaborator.sample_item_id,
                            "last_active_at": collaborator.last_active_at.isoformat() if collaborator.last_active_at else None,
                        }
                        for collaborator in collaborator_map.get(item.id, [])
                    ],
                }
                for item in items
            ],
        )
        return [
            self._to_annotation_response(item, collaborator_map.get(item.id, []))
            for item in items
        ], total

    async def get_home_summary(self, db: AsyncSession) -> AnnotationSummaryResponse:
        total = (
            await db.execute(
                select(func.count()).select_from(Annotation).where(Annotation.is_deleted == False)
            )
        ).scalar() or 0
        items, _ = await crud.get_annotations(db, 0, 5)
        collaborator_map = self._get_presence_summary_map([item.id for item in items])
        return AnnotationSummaryResponse(
            total=int(total),
            recent_annotations=[
                self._to_annotation_response(item, collaborator_map.get(item.id, []))
                for item in items
            ],
        )

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
        collaborators = self._get_presence_summaries(annotation_id)
        return self._to_annotation_response(ann, collaborators)

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
        raw_items = await self.ai_pipeline_service.list_assist_template_detail_descriptors(db)
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
    ) -> list[AnnotationAssistPipelineDetailResponse]:
        raw_items = await self.ai_pipeline_service.list_assist_template_detail_descriptors(db)
        items: list[AnnotationAssistPipelineDetailResponse] = []
        for item in raw_items:
            parsed = self._parse_pipeline_descriptor(item)
            if parsed is None:
                continue
            items.append(
                AnnotationAssistPipelineDetailResponse(
                    **parsed.model_dump(mode="python"),
                    steps=self._parse_pipeline_steps(item),
                )
            )
        return items

    async def list_home_platform_assist_pipeline_details(
        self,
        db: AsyncSession,
    ) -> list[AnnotationAssistPipelineDetailResponse]:
        raw_items = await self.ai_pipeline_service.list_home_assist_template_descriptors(db)
        items: list[AnnotationAssistPipelineDetailResponse] = []
        for item in raw_items:
            parsed = self._parse_pipeline_descriptor(item)
            if parsed is None:
                continue
            items.append(
                AnnotationAssistPipelineDetailResponse(
                    **parsed.model_dump(mode="python"),
                    steps=self._parse_pipeline_steps(item),
                )
            )
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

    async def create_collaboration_session(
        self,
        db: AsyncSession,
        annotation_id: int,
        data: AnnotationCollaborationSessionRequest,
    ) -> AnnotationCollaborationSessionResponse:
        await self._get_detection_annotation_for_collaboration(db, annotation_id)
        now = datetime.now()

        if data.token:
            collaborator = await crud.get_annotation_collaborator_by_token(db, annotation_id, data.token)
            if collaborator and collaborator.status == "active":
                collaborator = await crud.update_annotation_collaborator(
                    db,
                    collaborator.id,
                    last_active_at=now,
                )
                return AnnotationCollaborationSessionResponse(
                    collaborator=self._to_collaborator_response(collaborator)
                )

        count = await crud.count_annotation_collaborators(db, annotation_id)
        collaborator = await crud.create_annotation_collaborator(
            db,
            annotation_id=annotation_id,
            display_name=f"标注员-{count + 1:03d}",
            token=secrets.token_urlsafe(32),
            status="active",
            last_active_at=now,
        )
        return AnnotationCollaborationSessionResponse(
            collaborator=self._to_collaborator_response(collaborator)
        )

    async def heartbeat_annotation_presence(
        self,
        db: AsyncSession,
        annotation_id: int,
        data: AnnotationPresenceHeartbeatRequest,
    ) -> list[AnnotationCollaboratorSummaryResponse]:
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")

        participant_id = data.participant_id.strip()
        display_name = data.display_name.strip() or participant_id
        now = datetime.now()
        entries = _annotation_presence.setdefault(annotation_id, {})
        entries[participant_id] = AnnotationPresenceEntry(
            annotation_id=annotation_id,
            participant_id=participant_id,
            display_name=display_name,
            sample_item_id=data.sample_item_id,
            last_active_at=now,
        )
        collaborators = self._get_presence_summaries(annotation_id, now)
        logger.info(
            "[annotation:presence:heartbeat] annotation_id={} participant_id={} display_name={} sample_item_id={} online_count={}",
            annotation_id,
            participant_id,
            display_name,
            data.sample_item_id,
            len(collaborators),
        )
        return collaborators

    async def leave_annotation_presence(
        self,
        annotation_id: int,
        participant_id: str,
    ) -> list[AnnotationCollaboratorSummaryResponse]:
        normalized_participant_id = participant_id.strip()
        entries = _annotation_presence.get(annotation_id)
        if entries and normalized_participant_id:
            entries.pop(normalized_participant_id, None)
            if not entries:
                _annotation_presence.pop(annotation_id, None)
        collaborators = self._get_presence_summaries(annotation_id)
        logger.info(
            "[annotation:presence:leave] annotation_id={} participant_id={} online_count={}",
            annotation_id,
            normalized_participant_id,
            len(collaborators),
        )
        return collaborators

    async def claim_collaboration_samples(
        self,
        db: AsyncSession,
        annotation_id: int,
        data: AnnotationCollaborationClaimRequest,
    ) -> AnnotationCollaborationClaimResponse:
        ann = await self._get_detection_annotation_for_collaboration(db, annotation_id)
        collaborator = await self._get_active_collaborator(db, annotation_id, data.collaborator_token)
        now = datetime.now()
        lease_expires_at = self._next_lease_expires_at(now)

        await crud.update_annotation_collaborator(
            db,
            collaborator.id,
            last_active_at=now,
        )

        completed_subq = (
            select(AnnotationRecord.sample_item_id)
            .where(
                AnnotationRecord.annotation_id == annotation_id,
                AnnotationRecord.is_deleted == False,
                AnnotationRecord.status.in_(["saved", "reviewed"]),
            )
        )
        active_assignment_subq = (
            select(AnnotationSampleAssignment.sample_item_id)
            .where(
                AnnotationSampleAssignment.annotation_id == annotation_id,
                AnnotationSampleAssignment.is_deleted == False,
                AnnotationSampleAssignment.status.in_(["assigned", "in_progress"]),
                AnnotationSampleAssignment.lease_expires_at > now,
            )
        )
        candidate_stmt = (
            select(SampleItem.id)
            .where(
                SampleItem.dataset_id == ann.dataset_id,
                SampleItem.is_deleted == False,
                SampleItem.item_type == "image",
                ~SampleItem.id.in_(completed_subq),
                ~SampleItem.id.in_(active_assignment_subq),
            )
            .order_by(SampleItem.sort_order.asc(), SampleItem.created_at.asc(), SampleItem.id.asc())
            .limit(data.batch_size * 3)
            .with_for_update(skip_locked=True)
        )
        candidate_ids = [int(item) for item in (await db.execute(candidate_stmt)).scalars().all()]

        assigned_count = 0
        for sample_item_id in candidate_ids:
            assignment = await crud.get_annotation_assignment_for_update(db, annotation_id, sample_item_id)
            if assignment:
                if assignment.status == "submitted":
                    continue
                if (
                    assignment.status in {"assigned", "in_progress"}
                    and assignment.lease_expires_at
                    and assignment.lease_expires_at > now
                    and assignment.collaborator_id != collaborator.id
                ):
                    continue
                await crud.update_annotation_assignment(
                    db,
                    assignment.id,
                    collaborator_id=collaborator.id,
                    status="assigned",
                    lease_expires_at=lease_expires_at,
                )
            else:
                await crud.create_annotation_assignment(
                    db,
                    annotation_id=annotation_id,
                    sample_item_id=sample_item_id,
                    collaborator_id=collaborator.id,
                    status="assigned",
                    lease_expires_at=lease_expires_at,
                )
            assigned_count += 1
            if assigned_count >= data.batch_size:
                break

        return AnnotationCollaborationClaimResponse(assigned_count=assigned_count)

    async def list_collaboration_samples(
        self,
        db: AsyncSession,
        annotation_id: int,
        collaborator_token: str,
        page: int = 1,
        page_size: int = 100,
    ) -> AnnotationCollaborationSamplesResponse:
        await self._get_detection_annotation_for_collaboration(db, annotation_id)
        collaborator = await self._get_active_collaborator(db, annotation_id, collaborator_token)
        now = datetime.now()
        lease_expires_at = self._next_lease_expires_at(now)
        await crud.update_annotation_collaborator(db, collaborator.id, last_active_at=now)

        offset = (page - 1) * page_size
        assignments, total = await crud.get_annotation_assignments_by_collaborator(
            db,
            annotation_id,
            collaborator.id,
            offset,
            page_size,
        )
        for assignment in assignments:
            if assignment.status in {"assigned", "in_progress"}:
                await crud.update_annotation_assignment(
                    db,
                    assignment.id,
                    status="in_progress",
                    lease_expires_at=lease_expires_at,
                )

        sample_ids = [assignment.sample_item_id for assignment in assignments]
        samples: list[SampleItemResponse] = []
        records: list[AnnotationRecordResponse] = []
        if sample_ids:
            sample_result = await db.execute(
                select(SampleItem)
                .where(
                    SampleItem.id.in_(sample_ids),
                    SampleItem.is_deleted == False,
                )
            )
            sample_map = {item.id: item for item in sample_result.scalars().all()}
            samples = [
                await self._to_sample_response(db, sample_map[assignment.sample_item_id])
                for assignment in assignments
                if assignment.sample_item_id in sample_map
            ]
            raw_records = await crud.get_annotation_records_by_sample_ids(db, annotation_id, sample_ids)
            records = await asyncio.gather(
                *(self._build_annotation_record_response(record) for record in raw_records)
            ) if raw_records else []

        return AnnotationCollaborationSamplesResponse(
            collaborator=self._to_collaborator_response(collaborator),
            samples=samples,
            records=records,
            assignments=[self._to_assignment_response(assignment) for assignment in assignments],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def get_collaboration_stats(
        self,
        db: AsyncSession,
        annotation_id: int,
        collaborator_token: str,
    ) -> AnnotationCollaborationStatsResponse:
        ann = await self._get_detection_annotation_for_collaboration(db, annotation_id)
        collaborator = await self._get_active_collaborator(db, annotation_id, collaborator_token)
        now = datetime.now()

        total = (
            await db.execute(
                select(func.count())
                .select_from(SampleItem)
                .where(
                    SampleItem.dataset_id == ann.dataset_id,
                    SampleItem.is_deleted == False,
                    SampleItem.item_type == "image",
                )
            )
        ).scalar() or 0
        completed = (
            await db.execute(
                select(func.count(func.distinct(AnnotationRecord.sample_item_id)))
                .select_from(AnnotationRecord)
                .where(
                    AnnotationRecord.annotation_id == annotation_id,
                    AnnotationRecord.is_deleted == False,
                    AnnotationRecord.status.in_(["saved", "reviewed"]),
                )
            )
        ).scalar() or 0
        assigned_to_me = (
            await db.execute(
                select(func.count())
                .select_from(AnnotationSampleAssignment)
                .where(
                    AnnotationSampleAssignment.annotation_id == annotation_id,
                    AnnotationSampleAssignment.collaborator_id == collaborator.id,
                    AnnotationSampleAssignment.is_deleted == False,
                    AnnotationSampleAssignment.status != "released",
                )
            )
        ).scalar() or 0
        pending_mine = (
            await db.execute(
                select(func.count())
                .select_from(AnnotationSampleAssignment)
                .where(
                    AnnotationSampleAssignment.annotation_id == annotation_id,
                    AnnotationSampleAssignment.collaborator_id == collaborator.id,
                    AnnotationSampleAssignment.is_deleted == False,
                    AnnotationSampleAssignment.status.in_(["assigned", "in_progress"]),
                )
            )
        ).scalar() or 0
        active_assignments = await crud.count_active_annotation_assignments(db, annotation_id, now)
        available = max(int(total) - int(completed) - active_assignments, 0)
        return AnnotationCollaborationStatsResponse(
            total=int(total),
            completed=int(completed),
            assigned_to_me=int(assigned_to_me),
            pending_mine=int(pending_mine),
            available=available,
        )

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
        if data.collab_state and data.collab_state_sample_item_id != data.sample_item_id:
            raise BadRequestException("collab_state sample_item_id does not match current sample")
        collaboration_assignment = await self._validate_collaboration_save(db, ann, data)

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
        if collaboration_assignment:
            now = datetime.now()
            await crud.update_annotation_assignment(
                db,
                collaboration_assignment.id,
                status="submitted",
                submitted_at=now,
                lease_expires_at=self._next_lease_expires_at(now),
                collab_state=data.collab_state,
            )
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
        logger.info(
            "Assist annotation start annotation_id={} sample_item_id={} requested_pipeline_id={} requested_binding_id={} shape={} target_classes={} request_param_keys={}",
            annotation_id,
            data.sample_item_id,
            data.pipeline_id,
            data.binding_id,
            shape,
            selected_classes,
            sorted((data.params or {}).keys()),
        )
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

        file_name = asset.file_name or sample_item.item_key
        exists = await self.s3.file_exists(asset.save_path, bucket_type="datasets")
        if not exists:
            raise NotFoundException(f"Asset for sample {data.sample_item_id} not found")
        image_url = await self.s3.get_presigned_url(asset.save_path, bucket_type="datasets")
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
                    "url": image_url,
                    "mime_type": asset.mime_type or "image/jpeg",
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
            "Assist annotation request annotation_id={} file={} pipeline={} binding_id={} shape={} classes={} prompt_present={} prompt_length={}",
            annotation_id,
            file_name,
            pipeline.id,
            binding_context.get("binding_id") if binding_context else None,
            shape,
            selected_classes,
            bool(request_payload["input"]["prompt"]),
            len(str(request_payload["input"]["prompt"] or "")),
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
            logger.info(
                "Assist annotation dispatch annotation_id={} pipeline={} binding_id={} rpc_payload_keys={}",
                annotation_id,
                pipeline.id,
                binding_context.get("binding_id") if binding_context else None,
                sorted(rpc_payload.keys()),
            )
            payload = await asyncio.to_thread(
                self.assist_rpc_client.call,
                rpc_payload,
                get_settings().ai_pipeline_runtime.timeout,
            )
        except Exception as exc:
            logger.error(f"Failed to call ai_pipeline_runtime by MQ: {exc}")
            raise BadRequestException(f"ai_pipeline_runtime unavailable: {exc}")

        logger.info(
            "Assist annotation pipeline response annotation_id={} pipeline={} payload_type={}",
            annotation_id,
            pipeline.id,
            type(payload).__name__,
        )
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
        logger.info(
            "Assist annotation result annotation_id={} pipeline={} annotation_count={} image_width={} image_height={} has_debug={}",
            annotation_id,
            pipeline.id,
            len(items),
            int(result.get("image_width", 0) or 0),
            int(result.get("image_height", 0) or 0),
            isinstance(result.get("raw"), dict),
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
        logger.info(
            "Resolving assist pipeline annotation_id={} shape={} requested_pipeline_id={} requested_binding_id={} candidate_count={}",
            ann.id,
            shape,
            requested_pipeline_id,
            requested_binding_id,
            len(pipelines),
        )
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
            logger.info(
                "Assist binding context linked annotation_id={} binding_id={} binding_pipeline_id={}",
                ann.id,
                binding_context.get("binding_id"),
                binding_pipeline_id,
            )

        pipeline_id = requested_pipeline_id or binding_pipeline_id or getattr(ann, "assist_pipeline", None)
        if pipeline_id:
            matched = next((item for item in pipelines if item.id == pipeline_id), None)
            if matched:
                if getattr(ann, "assist_pipeline", None) != matched.id:
                    await crud.update_annotation(db, ann.id, assist_pipeline=matched.id)
                logger.info(
                    "Assist pipeline resolved annotation_id={} pipeline_id={} source={} binding_id={}",
                    ann.id,
                    matched.id,
                    "requested" if requested_pipeline_id else ("binding" if binding_pipeline_id == matched.id else "annotation"),
                    binding_context.get("binding_id") if binding_context and binding_pipeline_id == matched.id else None,
                )
                return {
                    "pipeline": matched,
                    "binding_context": binding_context if binding_pipeline_id == matched.id else None,
                }
            logger.warning(
                "Assist pipeline unsupported annotation_id={} pipeline_id={} shape={} available_pipeline_ids={}",
                ann.id,
                pipeline_id,
                shape,
                [item.id for item in pipelines],
            )
            raise BadRequestException(f"annotation assist pipeline `{pipeline_id}` does not support current annotation shape")

        selected = pipelines[0]
        await crud.update_annotation(db, ann.id, assist_pipeline=selected.id)
        logger.info(
            "Assist pipeline auto-selected annotation_id={} pipeline_id={}",
            ann.id,
            selected.id,
        )
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
            logger.debug(
                "No assist binding configured annotation_id={} requested_binding_id={}",
                ann.id,
                requested_binding_id,
            )
            return None
        logger.info(
            "Loading assist binding context annotation_id={} binding_id={} source={}",
            ann.id,
            binding_id,
            "requested" if requested_binding_id else "default",
        )
        try:
            binding_context = await self.ai_pipeline_service.get_binding_execution_context(
                db,
                binding_id,
            )
        except Exception as exc:
            logger.warning(
                "Failed to load annotation AI pipeline binding {} for annotation {}: {}",
                binding_id,
                ann.id,
                exc,
            )
            return None
        if not binding_context:
            logger.warning(
                "Empty assist binding context annotation_id={} binding_id={}",
                ann.id,
                binding_id,
            )
            return None
        if binding_context.get("binding_type") != "annotation_project":
            logger.warning(
                "Ignore AI pipeline binding {} for annotation {} due to binding_type={}",
                binding_id,
                ann.id,
                binding_context.get("binding_type"),
            )
            return None
        if int(binding_context.get("binding_target_id") or 0) != int(ann.id):
            logger.warning(
                "Ignore AI pipeline binding {} for annotation {} due to binding_target_id={}",
                binding_id,
                ann.id,
                binding_context.get("binding_target_id"),
            )
            return None
        logger.info(
            "Loaded assist binding context annotation_id={} binding_id={} binding_type={} binding_target_id={} template_key={} template_version={} runtime_default_keys={} resource_binding_keys={}",
            ann.id,
            binding_id,
            binding_context.get("binding_type"),
            binding_context.get("binding_target_id"),
            binding_context.get("template_key"),
            binding_context.get("template_version"),
            sorted((binding_context.get("runtime_input_defaults_json") or {}).keys())
            if isinstance(binding_context.get("runtime_input_defaults_json"), dict)
            else [],
            sorted((binding_context.get("resource_bindings_json") or {}).keys())
            if isinstance(binding_context.get("resource_bindings_json"), dict)
            else [],
        )
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
        runtime_default_keys: list[str] = []
        binding_id = None
        if binding_context:
            runtime_defaults = binding_context.get("runtime_input_defaults_json")
            if isinstance(runtime_defaults, dict):
                merged.update(runtime_defaults)
                runtime_default_keys = sorted(runtime_defaults.keys())

            resource_bindings = binding_context.get("resource_bindings_json")
            if resource_bindings is not None:
                merged["resource_bindings"] = resource_bindings
                merged["ai_pipeline_resource_bindings"] = resource_bindings

            binding_id = binding_context.get("binding_id")
            merged["ai_pipeline_binding_id"] = binding_id
            merged["ai_pipeline_template_key"] = binding_context.get("template_key")
            merged["ai_pipeline_template_version"] = binding_context.get("template_version")

        merged.update(request_params)
        merged["classes"] = selected_classes
        if ann.prompt and "prompt" not in merged:
            merged["prompt"] = ann.prompt
        logger.info(
            "Merged assist runtime params annotation_id={} binding_id={} default_keys={} request_keys={} final_keys={}",
            ann.id,
            binding_id,
            runtime_default_keys,
            sorted(request_params.keys()),
            sorted(merged.keys()),
        )
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
        logger.info(
            "Extracting pipeline annotation result pipeline_id={} payload_type={}",
            pipeline_id,
            type(payload).__name__,
        )
        if not isinstance(payload, dict):
            logger.warning(
                "Pipeline annotation result payload is not dict pipeline_id={} payload_type={}",
                pipeline_id,
                type(payload).__name__,
            )
            return {"annotations": [], "raw": {"pipeline_payload": payload}}
        if "annotations" in payload:
            logger.info(
                "Pipeline annotation result found at root pipeline_id={} keys={}",
                pipeline_id,
                sorted(payload.keys()),
            )
            return payload

        context = payload.get("context")
        if not isinstance(context, dict):
            logger.warning(
                "Pipeline annotation result payload has no context pipeline_id={} keys={}",
                pipeline_id,
                sorted(payload.keys()),
            )
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
                logger.info(
                    "Pipeline annotation result found in context pipeline_id={} candidate_key={} candidate_keys={}",
                    pipeline_id,
                    key,
                    sorted(candidate.keys()),
                )
                return candidate

        for candidate_key, candidate in reversed(list(context.items())):
            if isinstance(candidate, dict) and "annotations" in candidate:
                logger.info(
                    "Pipeline annotation result fallback hit pipeline_id={} candidate_key={} candidate_keys={}",
                    pipeline_id,
                    candidate_key,
                    sorted(candidate.keys()),
                )
                return candidate
        logger.warning(
            "Pipeline annotation result not found pipeline_id={} context_keys={}",
            pipeline_id,
            sorted(context.keys()),
        )
        return {"annotations": [], "raw": {"pipeline_payload": payload}}

    async def _build_annotation_record_response(self, record) -> AnnotationRecordResponse:
        content = await self._load_annotation_record_content(record.annotation_type, record.content)
        return self._to_annotation_record_response(record, content)

    async def _get_detection_annotation_for_collaboration(
        self,
        db: AsyncSession,
        annotation_id: int,
    ):
        ann = await crud.get_annotation_by_id(db, annotation_id)
        if not ann:
            raise NotFoundException(f"Annotation {annotation_id} not found")
        if ann.annotation_type != AnnotationType.DETECTION:
            raise BadRequestException("collaboration MVP currently only supports detection projects")
        if not ann.dataset_id:
            raise BadRequestException("collaboration requires annotation project dataset_id")
        return ann

    async def _get_active_collaborator(
        self,
        db: AsyncSession,
        annotation_id: int,
        token: str,
    ):
        normalized = (token or "").strip()
        if not normalized:
            raise ForbiddenException("collaborator token is required")
        collaborator = await crud.get_annotation_collaborator_by_token(db, annotation_id, normalized)
        if not collaborator or collaborator.status != "active":
            raise ForbiddenException("collaborator token is invalid")
        return collaborator

    async def _validate_collaboration_save(
        self,
        db: AsyncSession,
        ann,
        data: AnnotationRecordSave,
    ):
        if not data.collaborator_token:
            return None
        await self._get_detection_annotation_for_collaboration(db, ann.id)
        collaborator = await self._get_active_collaborator(db, ann.id, data.collaborator_token)
        assignment = await crud.get_annotation_assignment_for_update(
            db,
            ann.id,
            data.sample_item_id,
        )
        if not assignment or assignment.collaborator_id != collaborator.id:
            raise ForbiddenException("sample item is assigned to another collaborator")
        if assignment.status == "released":
            raise ForbiddenException("sample item assignment has been released")
        await crud.update_annotation_collaborator(
            db,
            collaborator.id,
            last_active_at=datetime.now(),
        )
        return assignment

    def _next_lease_expires_at(self, now: datetime | None = None) -> datetime:
        base_time = now or datetime.now()
        return base_time + timedelta(minutes=self.COLLABORATION_LEASE_MINUTES)

    def _get_presence_summary_map(
        self,
        annotation_ids: list[int],
    ) -> dict[int, list[AnnotationCollaboratorSummaryResponse]]:
        now = datetime.now()
        result: dict[int, list[AnnotationCollaboratorSummaryResponse]] = {}
        for annotation_id in annotation_ids:
            summaries = self._get_presence_summaries(annotation_id, now)
            if summaries:
                result[annotation_id] = summaries
        return result

    def _get_presence_summaries(
        self,
        annotation_id: int,
        now: datetime | None = None,
    ) -> list[AnnotationCollaboratorSummaryResponse]:
        entries = self._prune_presence(annotation_id, now or datetime.now())
        return [
            self._to_presence_summary_response(entry)
            for entry in sorted(entries.values(), key=lambda item: item.last_active_at, reverse=True)
        ]

    def _prune_presence(
        self,
        annotation_id: int,
        now: datetime,
    ) -> dict[str, AnnotationPresenceEntry]:
        entries = _annotation_presence.get(annotation_id)
        if not entries:
            return {}

        expires_before = now - timedelta(seconds=ANNOTATION_PRESENCE_TTL_SECONDS)
        expired_participant_ids = [
            participant_id
            for participant_id, entry in entries.items()
            if entry.last_active_at < expires_before
        ]
        for participant_id in expired_participant_ids:
            entries.pop(participant_id, None)
        if not entries:
            _annotation_presence.pop(annotation_id, None)
            return {}
        return entries

    def _to_annotation_response(
        self,
        annotation,
        collaborators: list[AnnotationCollaboratorSummaryResponse] | None = None,
    ) -> AnnotationResponse:
        response = AnnotationResponse.model_validate(annotation)
        response.collaborators = collaborators or []
        return response

    def _to_presence_summary_response(self, entry: AnnotationPresenceEntry) -> AnnotationCollaboratorSummaryResponse:
        return AnnotationCollaboratorSummaryResponse(
            annotation_id=entry.annotation_id,
            participant_id=entry.participant_id,
            display_name=entry.display_name,
            sample_item_id=entry.sample_item_id,
            last_active_at=entry.last_active_at,
        )

    def _to_collaborator_response(self, collaborator) -> AnnotationCollaboratorResponse:
        return AnnotationCollaboratorResponse(
            id=collaborator.id,
            annotation_id=collaborator.annotation_id,
            display_name=collaborator.display_name,
            token=collaborator.token,
            status=collaborator.status,
            last_active_at=collaborator.last_active_at,
            created_at=collaborator.created_at,
            updated_at=collaborator.updated_at,
        )

    def _to_assignment_response(self, assignment) -> AnnotationSampleAssignmentResponse:
        return AnnotationSampleAssignmentResponse(
            id=assignment.id,
            annotation_id=assignment.annotation_id,
            sample_item_id=assignment.sample_item_id,
            collaborator_id=assignment.collaborator_id,
            status=assignment.status,
            lease_expires_at=assignment.lease_expires_at,
            submitted_at=assignment.submitted_at,
            collab_state=assignment.collab_state,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
        )

    def _load_json_object(self, raw_value: Any) -> dict[str, Any] | None:
        if not raw_value:
            return None
        if isinstance(raw_value, dict):
            return raw_value
        try:
            parsed = json.loads(raw_value)
        except (TypeError, json.JSONDecodeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    async def _to_sample_response(self, db: AsyncSession, item) -> SampleItemResponse:
        asset_response = None
        if item.asset_id:
            asset = await db.scalar(
                select(Asset).where(
                    Asset.id == item.asset_id,
                    Asset.is_deleted == False,
                )
            )
            if asset:
                asset_response = AssetResponse(
                    id=asset.id,
                    dataset_id=asset.dataset_id,
                    asset_type=asset.asset_type,
                    file_name=asset.file_name,
                    save_path=asset.save_path,
                    mime_type=asset.mime_type,
                    size_bytes=asset.size_bytes,
                    meta_json=asset.meta_json,
                    created_at=asset.created_at,
                )
        return SampleItemResponse(
            id=item.id,
            dataset_id=item.dataset_id,
            asset_id=item.asset_id,
            item_type=item.item_type,
            item_key=item.item_key,
            locator=self._load_json_object(item.locator),
            payload=self._load_json_object(item.payload),
            sort_order=item.sort_order,
            created_at=item.created_at,
            updated_at=item.updated_at,
            asset=asset_response,
        )

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
