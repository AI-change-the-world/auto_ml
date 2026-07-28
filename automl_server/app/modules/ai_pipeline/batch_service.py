"""Dataset batch annotation orchestration.

The API service owns task state and annotation persistence. The sandbox only
receives immutable chunk payloads and publishes structured results back via MQ.
"""
from __future__ import annotations

import asyncio
import json
import math
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BadRequestException, NotFoundException
from app.db.models import (
    Annotation,
    AnnotationRecord,
    AiPipelineBatchRun,
    AiPipelineBatchRunEvent,
    AiPipelineBatchRunItem,
    Asset,
    Dataset,
    SampleItem,
)
from app.mq.publisher import get_publisher
from app.utils.annotation_classes import parse_annotation_classes

from .batch_schemas import (
    AiPipelineBatchRunCreate,
    AiPipelineBatchRunEventResponse,
    AiPipelineBatchRunItemResponse,
    AiPipelineBatchRunResponse,
    AiPipelineBatchScriptResponse,
)
from .batch_scripts import get_batch_script, list_batch_scripts


TERMINAL_ITEM_STATUSES = {"succeeded", "failed", "skipped", "canceled"}


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _load_json(value: Any, fallback: Any) -> Any:
    if value is None or value == "":
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


class BatchAnnotationService:
    def list_scripts(self) -> list[AiPipelineBatchScriptResponse]:
        return [AiPipelineBatchScriptResponse.model_validate(item) for item in list_batch_scripts()]

    async def create_run(
        self,
        db: AsyncSession,
        data: AiPipelineBatchRunCreate,
    ) -> AiPipelineBatchRunResponse:
        script = get_batch_script(data.script_key)
        if not script:
            raise BadRequestException("batch annotation script is not available")

        dataset = await db.scalar(
            select(Dataset).where(Dataset.id == data.dataset_id, Dataset.is_deleted == False)
        )
        if not dataset:
            raise NotFoundException(f"Dataset {data.dataset_id} not found")
        if dataset.data_type not in script["supported_data_types"]:
            raise BadRequestException("selected script does not support this dataset type")

        annotation = await db.scalar(
            select(Annotation).where(Annotation.id == data.annotation_id, Annotation.is_deleted == False)
        )
        if not annotation:
            raise NotFoundException(f"Annotation {data.annotation_id} not found")
        if annotation.dataset_id != dataset.id:
            raise BadRequestException("annotation project must belong to the selected dataset")
        if annotation.annotation_type not in script["supported_annotation_types"]:
            raise BadRequestException("selected script does not support this annotation type")

        samples = await self._load_samples(db, data)
        if not samples:
            raise BadRequestException("no samples match the selected scope")

        sample_ids = [sample.id for sample, _ in samples]
        existing_records = await self._load_existing_records(db, annotation.id, sample_ids)
        if data.selection_mode == "unannotated":
            samples = [item for item in samples if item[0].id not in existing_records]
            if not samples:
                raise BadRequestException("no unannotated samples match the selected scope")
        annotation_snapshot = {
            "annotation_id": annotation.id,
            "annotation_type": annotation.annotation_type,
            "classes": parse_annotation_classes(annotation.classes),
            "prompt": annotation.prompt,
        }
        now = datetime.now()
        run = AiPipelineBatchRun(
            run_id=f"batch_{uuid.uuid4().hex}",
            dataset_id=dataset.id,
            annotation_id=annotation.id,
            script_key=script["key"],
            script_version=script["version"],
            status="queued",
            selection_mode=data.selection_mode,
            overwrite_policy=data.overwrite_policy,
            batch_size=data.batch_size,
            parallelism=data.parallelism,
            total_count=len(samples),
            script_params_json=_dump_json(data.script_params),
            annotation_snapshot_json=_dump_json(annotation_snapshot),
        )
        db.add(run)
        await db.flush()

        skipped_count = 0
        for sample, asset in samples:
            existing = existing_records.get(sample.id)
            status, reason = self._resolve_item_status(existing, data.overwrite_policy, asset)
            if status == "skipped":
                skipped_count += 1
            item_snapshot = {
                "sample_item_id": sample.id,
                "item_key": sample.item_key,
                "asset_path": asset.save_path if asset else None,
                "asset_mime_type": asset.mime_type if asset else None,
                "asset_file_name": asset.file_name if asset else sample.item_key,
                "item_type": sample.item_type,
                "locator": _load_json(sample.locator, {}),
                "payload": _load_json(sample.payload, {}),
            }
            db.add(
                AiPipelineBatchRunItem(
                    batch_run_id=run.id,
                    sample_item_id=sample.id,
                    item_key=sample.item_key,
                    asset_path=item_snapshot["asset_path"],
                    asset_mime_type=item_snapshot["asset_mime_type"],
                    input_snapshot_json=_dump_json(item_snapshot),
                    status=status,
                    error_message=reason,
                    finished_at=now if status == "skipped" else None,
                )
            )

        run.skipped_count = skipped_count
        run.progress = self._calculate_progress(run.total_count, skipped_count)
        await self._append_event(
            db,
            run.id,
            "queued",
            {"message": "batch run created", "total_count": run.total_count, "skipped_count": skipped_count},
        )
        await db.commit()
        await db.refresh(run)
        await self._dispatch_available_chunks(db, run)
        return self._to_run_response(run)

    async def list_runs(
        self,
        db: AsyncSession,
        *,
        dataset_id: int | None = None,
        annotation_id: int | None = None,
        limit: int = 50,
    ) -> list[AiPipelineBatchRunResponse]:
        conditions = [AiPipelineBatchRun.is_deleted == False]
        if dataset_id:
            conditions.append(AiPipelineBatchRun.dataset_id == dataset_id)
        if annotation_id:
            conditions.append(AiPipelineBatchRun.annotation_id == annotation_id)
        stmt = (
            select(AiPipelineBatchRun)
            .where(*conditions)
            .order_by(AiPipelineBatchRun.created_at.desc(), AiPipelineBatchRun.id.desc())
            .limit(limit)
        )
        runs = list((await db.execute(stmt)).scalars().all())
        return [self._to_run_response(item) for item in runs]

    async def get_run(self, db: AsyncSession, run_id: str) -> AiPipelineBatchRunResponse:
        run = await self._get_run(db, run_id)
        return self._to_run_response(run)

    async def list_items(
        self,
        db: AsyncSession,
        run_id: str,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[AiPipelineBatchRunItemResponse], int]:
        run = await self._get_run(db, run_id)
        conditions = [
            AiPipelineBatchRunItem.batch_run_id == run.id,
            AiPipelineBatchRunItem.is_deleted == False,
        ]
        if status:
            conditions.append(AiPipelineBatchRunItem.status == status)
        count_stmt = select(func.count()).select_from(AiPipelineBatchRunItem).where(*conditions)
        total = int((await db.execute(count_stmt)).scalar() or 0)
        stmt = (
            select(AiPipelineBatchRunItem)
            .where(*conditions)
            .order_by(AiPipelineBatchRunItem.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list((await db.execute(stmt)).scalars().all())
        return [self._to_item_response(item) for item in items], total

    async def list_events(
        self,
        db: AsyncSession,
        run_id: str,
        *,
        after_id: int = 0,
        limit: int = 100,
    ) -> list[AiPipelineBatchRunEventResponse]:
        run = await self._get_run(db, run_id)
        stmt = (
            select(AiPipelineBatchRunEvent)
            .where(
                AiPipelineBatchRunEvent.batch_run_id == run.id,
                AiPipelineBatchRunEvent.id > after_id,
                AiPipelineBatchRunEvent.is_deleted == False,
            )
            .order_by(AiPipelineBatchRunEvent.id.asc())
            .limit(limit)
        )
        events = list((await db.execute(stmt)).scalars().all())
        return [
            AiPipelineBatchRunEventResponse(
                id=event.id,
                event_type=event.event_type,
                event_payload=_load_json(event.event_payload, event.event_payload),
                created_at=event.created_at,
            )
            for event in events
        ]

    async def cancel_run(self, db: AsyncSession, run_id: str) -> AiPipelineBatchRunResponse:
        run = await self._get_run(db, run_id)
        if run.status in {"succeeded", "failed", "canceled"}:
            return self._to_run_response(run)

        now = datetime.now()
        pending_items = list(
            (
                await db.execute(
                    select(AiPipelineBatchRunItem).where(
                        AiPipelineBatchRunItem.batch_run_id == run.id,
                        AiPipelineBatchRunItem.status.in_(["pending", "queued"]),
                        AiPipelineBatchRunItem.is_deleted == False,
                    )
                )
            ).scalars().all()
        )
        for item in pending_items:
            item.status = "canceled"
            item.finished_at = now
            item.error_message = "canceled by user"
        run.cancel_requested = True
        run.status = "canceled"
        run.finished_at = now
        await self._refresh_run_counts(db, run)
        await self._append_event(db, run.id, "canceled", {"message": "canceled by user"})
        await db.commit()
        await db.refresh(run)
        return self._to_run_response(run)

    async def handle_worker_progress(self, db: AsyncSession, payload: dict[str, Any]) -> None:
        run = await self._find_run(db, str(payload.get("run_id") or ""))
        if not run or run.cancel_requested:
            return
        if run.status == "queued":
            run.status = "running"
            run.started_at = run.started_at or datetime.now()
        terminal_stmt = select(func.count()).select_from(AiPipelineBatchRunItem).where(
            AiPipelineBatchRunItem.batch_run_id == run.id,
            AiPipelineBatchRunItem.status.in_(TERMINAL_ITEM_STATUSES),
            AiPipelineBatchRunItem.is_deleted == False,
        )
        completed_count = int((await db.execute(terminal_stmt)).scalar() or 0)
        current_chunk_progress = min(
            max(int(payload.get("processed") or 0), 0),
            max(int(payload.get("total") or 0), 0),
        )
        run.progress = max(
            run.progress,
            self._calculate_progress(run.total_count, completed_count + current_chunk_progress),
        )
        await self._append_event(
            db,
            run.id,
            "progress",
            {
                "chunk_key": payload.get("chunk_key"),
                "processed": payload.get("processed"),
                "total": payload.get("total"),
                "message": payload.get("message"),
            },
        )
        await db.commit()

    async def handle_worker_result(self, db: AsyncSession, payload: dict[str, Any]) -> None:
        run = await self._find_run(db, str(payload.get("run_id") or ""))
        if not run:
            return
        chunk_key = str(payload.get("chunk_key") or "")
        if not chunk_key:
            return

        items = list(
            (
                await db.execute(
                    select(AiPipelineBatchRunItem).where(
                        AiPipelineBatchRunItem.batch_run_id == run.id,
                        AiPipelineBatchRunItem.chunk_key == chunk_key,
                        AiPipelineBatchRunItem.is_deleted == False,
                    )
                )
            ).scalars().all()
        )
        if not items:
            return

        now = datetime.now()
        if run.cancel_requested:
            for item in items:
                if item.status == "queued":
                    item.status = "canceled"
                    item.finished_at = now
            await self._refresh_run_counts(db, run)
            await db.commit()
            return

        if run.status == "queued":
            run.status = "running"
            run.started_at = now
        results = payload.get("results") if isinstance(payload.get("results"), list) else []
        result_by_item_id = {
            int(result["batch_item_id"]): result
            for result in results
            if isinstance(result, dict) and str(result.get("batch_item_id", "")).isdigit()
        }
        for item in items:
            result = result_by_item_id.get(item.id)
            if result is None:
                item.status = "failed"
                item.error_message = "sandbox did not return a result for this sample"
                item.finished_at = now
                continue
            await self._apply_item_result(db, run, item, result, now)

        await self._refresh_run_counts(db, run)
        await self._append_event(
            db,
            run.id,
            "result",
            {
                "chunk_key": chunk_key,
                "succeeded_count": run.succeeded_count,
                "failed_count": run.failed_count,
                "skipped_count": run.skipped_count,
                "progress": run.progress,
            },
        )
        await db.commit()
        await db.refresh(run)
        if run.status not in {"succeeded", "failed", "canceled"}:
            await self._dispatch_available_chunks(db, run)

    async def _apply_item_result(
        self,
        db: AsyncSession,
        run: AiPipelineBatchRun,
        item: AiPipelineBatchRunItem,
        result: dict[str, Any],
        now: datetime,
    ) -> None:
        status = str(result.get("status") or "failed").strip().lower()
        item.result_json = _dump_json(result)
        item.finished_at = now
        if status == "skipped":
            item.status = "skipped"
            item.error_message = str(result.get("message") or "") or None
            return
        if status != "succeeded":
            item.status = "failed"
            item.error_message = str(result.get("error") or "sandbox script failed")
            return

        content = result.get("content")
        if not isinstance(content, dict):
            item.status = "failed"
            item.error_message = "sandbox result content must be a JSON object"
            return
        try:
            from app.modules.annotation.schemas import AnnotationRecordSave
            from app.modules.annotation.service import get_annotation_service

            record = await get_annotation_service().save_annotation_record(
                db,
                run.annotation_id,
                AnnotationRecordSave(sample_item_id=item.sample_item_id, content=content, status="saved"),
            )
        except Exception as exc:
            item.status = "failed"
            item.error_message = f"failed to save annotation result: {exc}"
            return
        item.status = "succeeded"
        item.annotation_record_id = record.id
        item.error_message = None

    async def _dispatch_available_chunks(self, db: AsyncSession, run: AiPipelineBatchRun) -> None:
        if run.cancel_requested or run.status in {"succeeded", "failed", "canceled"}:
            return
        active_stmt = (
            select(func.count(func.distinct(AiPipelineBatchRunItem.chunk_key)))
            .where(
                AiPipelineBatchRunItem.batch_run_id == run.id,
                AiPipelineBatchRunItem.status == "queued",
                AiPipelineBatchRunItem.chunk_key.is_not(None),
                AiPipelineBatchRunItem.is_deleted == False,
            )
        )
        active_count = int((await db.execute(active_stmt)).scalar() or 0)
        slots = max(run.parallelism - active_count, 0)
        if slots == 0:
            return

        pending_stmt = (
            select(AiPipelineBatchRunItem)
            .where(
                AiPipelineBatchRunItem.batch_run_id == run.id,
                AiPipelineBatchRunItem.status == "pending",
                AiPipelineBatchRunItem.is_deleted == False,
            )
            .order_by(AiPipelineBatchRunItem.id.asc())
            .limit(slots * run.batch_size)
        )
        pending_items = list((await db.execute(pending_stmt)).scalars().all())
        if not pending_items:
            await self._refresh_run_counts(db, run)
            await db.commit()
            return

        chunks: list[tuple[str, list[AiPipelineBatchRunItem]]] = []
        for index in range(0, len(pending_items), run.batch_size):
            chunk_items = pending_items[index:index + run.batch_size]
            chunk_key = f"{run.run_id}_{uuid.uuid4().hex[:12]}"
            for item in chunk_items:
                item.status = "queued"
                item.chunk_key = chunk_key
                item.attempt_count += 1
                item.started_at = item.started_at or datetime.now()
            chunks.append((chunk_key, chunk_items))
        await db.commit()

        annotation_snapshot = _load_json(run.annotation_snapshot_json, {})
        script_params = _load_json(run.script_params_json, {})
        for chunk_key, chunk_items in chunks:
            message = {
                "message_type": "pipeline.batch.execute",
                "service_name": "automl_server",
                "run_id": run.run_id,
                "chunk_key": chunk_key,
                "script_key": run.script_key,
                "script_version": run.script_version,
                "annotation": annotation_snapshot,
                "script_params": script_params,
                "items": [
                    {
                        "batch_item_id": item.id,
                        **_load_json(item.input_snapshot_json, {}),
                    }
                    for item in chunk_items
                ],
            }
            await asyncio.to_thread(get_publisher().publish_pipeline_batch_execute, message)

    async def _load_samples(
        self,
        db: AsyncSession,
        data: AiPipelineBatchRunCreate,
    ) -> list[tuple[SampleItem, Asset | None]]:
        conditions = [
            SampleItem.dataset_id == data.dataset_id,
            SampleItem.is_deleted == False,
        ]
        if data.selection_mode == "selected":
            selected_ids = list(dict.fromkeys(item for item in data.sample_item_ids if item > 0))
            if not selected_ids:
                raise BadRequestException("selected scope requires at least one sample")
            conditions.append(SampleItem.id.in_(selected_ids))
        stmt = (
            select(SampleItem, Asset)
            .outerjoin(
                Asset,
                and_(Asset.id == SampleItem.asset_id, Asset.is_deleted == False),
            )
            .where(*conditions)
            .order_by(SampleItem.id.asc())
        )
        rows = list((await db.execute(stmt)).all())
        if data.selection_mode == "selected":
            actual_ids = {sample.id for sample, _ in rows}
            missing_ids = sorted(set(data.sample_item_ids) - actual_ids)
            if missing_ids:
                raise BadRequestException("selected samples do not belong to this dataset")
        return rows

    async def _load_existing_records(
        self,
        db: AsyncSession,
        annotation_id: int,
        sample_ids: list[int],
    ) -> dict[int, AnnotationRecord]:
        if not sample_ids:
            return {}
        stmt = select(AnnotationRecord).where(
            AnnotationRecord.annotation_id == annotation_id,
            AnnotationRecord.sample_item_id.in_(sample_ids),
            AnnotationRecord.is_deleted == False,
        )
        records = list((await db.execute(stmt)).scalars().all())
        return {record.sample_item_id: record for record in records}

    def _resolve_item_status(
        self,
        existing: AnnotationRecord | None,
        overwrite_policy: str,
        asset: Asset | None,
    ) -> tuple[str, str | None]:
        if not asset or not asset.save_path:
            return "skipped", "sample has no readable asset"
        if not existing:
            return "pending", None
        if overwrite_policy == "overwrite_all":
            return "pending", None
        if overwrite_policy == "overwrite_draft" and existing.status == "draft":
            return "pending", None
        return "skipped", "existing annotation record was kept"

    async def _refresh_run_counts(self, db: AsyncSession, run: AiPipelineBatchRun) -> None:
        stmt = (
            select(AiPipelineBatchRunItem.status, func.count())
            .where(
                AiPipelineBatchRunItem.batch_run_id == run.id,
                AiPipelineBatchRunItem.is_deleted == False,
            )
            .group_by(AiPipelineBatchRunItem.status)
        )
        counts = {status: int(count) for status, count in (await db.execute(stmt)).all()}
        run.succeeded_count = counts.get("succeeded", 0)
        run.failed_count = counts.get("failed", 0)
        run.skipped_count = counts.get("skipped", 0)
        run.canceled_count = counts.get("canceled", 0)
        completed = sum(counts.get(status, 0) for status in TERMINAL_ITEM_STATUSES)
        run.progress = self._calculate_progress(run.total_count, completed)
        active_count = counts.get("pending", 0) + counts.get("queued", 0)
        if run.cancel_requested:
            run.status = "canceled"
            run.finished_at = run.finished_at or datetime.now()
        elif active_count == 0:
            run.finished_at = datetime.now()
            run.status = "failed" if run.succeeded_count == 0 and run.failed_count > 0 else "succeeded"
        elif run.status == "queued" and counts.get("queued", 0) > 0:
            run.status = "running"
            run.started_at = run.started_at or datetime.now()

    async def _get_run(self, db: AsyncSession, run_id: str) -> AiPipelineBatchRun:
        run = await self._find_run(db, run_id)
        if not run:
            raise NotFoundException(f"Batch run {run_id} not found")
        return run

    async def _find_run(self, db: AsyncSession, run_id: str) -> AiPipelineBatchRun | None:
        if not run_id:
            return None
        return await db.scalar(
            select(AiPipelineBatchRun).where(
                AiPipelineBatchRun.run_id == run_id,
                AiPipelineBatchRun.is_deleted == False,
            )
        )

    async def _append_event(
        self,
        db: AsyncSession,
        run_id: int,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        db.add(
            AiPipelineBatchRunEvent(
                batch_run_id=run_id,
                event_type=event_type,
                event_payload=_dump_json(payload),
            )
        )
        await db.flush()

    @staticmethod
    def _calculate_progress(total_count: int, completed_count: int) -> int:
        if total_count <= 0:
            return 100
        return min(100, math.floor(completed_count * 100 / total_count))

    @staticmethod
    def _to_run_response(run: AiPipelineBatchRun) -> AiPipelineBatchRunResponse:
        return AiPipelineBatchRunResponse(
            id=run.id,
            run_id=run.run_id,
            dataset_id=run.dataset_id,
            annotation_id=run.annotation_id,
            script_key=run.script_key,
            script_version=run.script_version,
            status=run.status,
            selection_mode=run.selection_mode,
            overwrite_policy=run.overwrite_policy,
            batch_size=run.batch_size,
            parallelism=run.parallelism,
            total_count=run.total_count,
            succeeded_count=run.succeeded_count,
            failed_count=run.failed_count,
            skipped_count=run.skipped_count,
            canceled_count=run.canceled_count,
            progress=run.progress,
            cancel_requested=run.cancel_requested,
            script_params=_load_json(run.script_params_json, {}),
            error_message=run.error_message,
            started_at=run.started_at,
            finished_at=run.finished_at,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @staticmethod
    def _to_item_response(item: AiPipelineBatchRunItem) -> AiPipelineBatchRunItemResponse:
        return AiPipelineBatchRunItemResponse(
            id=item.id,
            sample_item_id=item.sample_item_id,
            item_key=item.item_key,
            status=item.status,
            attempt_count=item.attempt_count,
            annotation_record_id=item.annotation_record_id,
            error_message=item.error_message,
            started_at=item.started_at,
            finished_at=item.finished_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )


_batch_annotation_service: BatchAnnotationService | None = None


def get_batch_annotation_service() -> BatchAnnotationService:
    global _batch_annotation_service
    if _batch_annotation_service is None:
        _batch_annotation_service = BatchAnnotationService()
    return _batch_annotation_service
