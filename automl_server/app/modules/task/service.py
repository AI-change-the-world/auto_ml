"""任务服务 - 与 model_trainer 通信"""
import asyncio
from datetime import datetime
import json
from typing import Any, List, Optional
from uuid import uuid4
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from jsonschema import Draft202012Validator, SchemaError
from app.common.exceptions import NotFoundException, BadRequestException, AppException
from app.common.constants import TaskStatus, TaskType, AnnotationType, DataType
from app.config.settings import get_settings
from app.db.models import Task
from app.db.models import Dataset, Annotation, Asset, SampleItem, AnnotationRecord, AvailableModel
from app.db.models import (
    TrainingRuntimeCodePackage,
    TrainingRuntimeExecution,
    TrainingRuntimeModelPackage,
)
from app.mq.publisher import get_publisher
from app.utils.annotation_classes import parse_annotation_classes
from app.utils.annotation_record_storage import (
    is_annotation_record_storage_path,
    parse_annotation_record_payload,
)
from app.utils.http_client import HttpClient
from app.utils.s3_delegate import get_s3_delegate
from .training_dataset_registration import TrainingDatasetSnapshotRegistrar
from .training_dataset_snapshot import TrainingDatasetSnapshotBuilder
from . import crud
from .schemas import (
    TaskCreate,
    RuntimeScriptTaskCreate,
    TaskResponse,
    TaskLogResponse,
    BaseModelResponse,
    TrainerStatusResponse,
    TaskSummaryResponse,
    TaskSourceResponse,
    TaskConfigPayload,
    TrainingHistoryCandidateResponse,
    TrainingHistoryQuery,
    TrainingDatasetSnapshotPreviewRequest,
    TrainingDatasetSnapshotPreviewResponse,
    TrainingDatasetSnapshotRegisterRequest,
    TrainingDatasetSnapshotRegistrationResponse,
    TrainingDatasetSnapshotManifest,
)

STALE_TASK_STATUSES = {TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.POST_PROCESS}
DEFAULT_STALE_TIMEOUT_SECONDS = 2 * 60 * 60


class TaskService:
    def __init__(self):
        self.s3 = get_s3_delegate()
        self._dataset_snapshot_builder = TrainingDatasetSnapshotBuilder()
        self._publisher = None
        self._trainer_client = None
        self._trainer_client_base_url = None
        self._trainer_client_timeout = None

    @property
    def publisher(self):
        if self._publisher is None:
            self._publisher = get_publisher()
        return self._publisher

    async def _get_trainer_client(self) -> HttpClient:
        settings = get_settings()
        base_url = settings.model_trainer.base_url
        timeout = settings.model_trainer.timeout

        if (
            self._trainer_client is None
            or self._trainer_client_base_url != base_url
            or self._trainer_client_timeout != timeout
        ):
            if self._trainer_client is not None:
                await self._trainer_client.close()
            self._trainer_client = HttpClient(
                base_url=base_url,
                timeout=timeout,
            )
            self._trainer_client_base_url = base_url
            self._trainer_client_timeout = timeout
        return self._trainer_client

    async def close(self):
        if self._trainer_client is not None:
            await self._trainer_client.close()
            self._trainer_client = None
            self._trainer_client_base_url = None
            self._trainer_client_timeout = None

    async def create_task(self, db: AsyncSession, data: TaskCreate) -> TaskResponse:
        """创建训练任务并通过 RabbitMQ 通知 model_trainer"""
        if data.task_type == TaskType.POSE:
            raise BadRequestException("pose task is not supported yet")
        if data.task_type not in {TaskType.DETECTION, TaskType.CLASSIFICATION, TaskType.SEGMENTATION}:
            raise BadRequestException(f"unsupported task_type: {data.task_type}")
        resolved_sources = await self._resolve_and_validate_sources(db, data)
        primary_source = resolved_sources[0]

        # 保存任务到数据库
        task = await crud.create_task(
            db,
            task_type=data.task_type,
            dataset_id=primary_source["dataset_id"],
            annotation_id=primary_source["annotation_id"],
            config=data.config,
            status=TaskStatus.PENDING.value,
        )
        await crud.create_task_sources(
            db,
            task_id=task.id,
            sources=[
                {
                    "dataset_id": source["dataset_id"],
                    "annotation_id": source["annotation_id"],
                    "source_order": source["source_order"],
                    "source_name": source["source_name"],
                }
                for source in resolved_sources
            ],
        )
        await db.commit()
        await db.refresh(task)

        config = json.loads(data.config) if data.config else {}
        if not isinstance(config, dict):
            raise BadRequestException("config must be a JSON object")
        try:
            normalized_config = TaskConfigPayload.model_validate(config).model_dump(
                mode="json",
                exclude_none=True,
            )
        except Exception as exc:
            raise BadRequestException(f"invalid task config: {exc}") from exc
        normalized_config = await self._attach_resume_model(db, normalized_config, data.task_type)
        classes = primary_source["classes"]
        serialized_sources = [self._serialize_training_source(source) for source in resolved_sources]
        train_request = {
            "task_id": task.id,
            "task_type": (
                "detection"
                if data.task_type == TaskType.DETECTION
                else "classification"
                if data.task_type == TaskType.CLASSIFICATION
                else "segmentation"
            ),
            "sources": serialized_sources,
            "classes": classes,
            "task_config": {
                **normalized_config,
                "dataset_id": primary_source["dataset_id"],
                "annotation_id": primary_source["annotation_id"],
                "source_count": len(serialized_sources),
                "sample_count": sum(len(source["samples"]) for source in resolved_sources),
                "classes": classes,
            },
        }

        # 通过 MQ 下发训练任务
        try:
            await asyncio.to_thread(self.publisher.publish_training_task, train_request)
            logger.info(f"Training task {task.id} queued by MQ")
        except Exception as e:
            logger.error(f"Failed to publish trainer task: {e}")
            task.status = TaskStatus.FAILED.value
            task.error_message = str(e)
            db.add(task)
            await db.commit()
            await db.refresh(task)
            raise AppException(
                code=503,
                message=f"Failed to queue training task: {e}",
                data=(await self._serialize_task(db, task)).model_dump(mode="json"),
            )

        return await self._serialize_task(db, task)

    async def create_runtime_script_task(
        self,
        db: AsyncSession,
        data: RuntimeScriptTaskCreate,
    ) -> TaskResponse:
        """Queue a user package on the dedicated runtime worker.

        All catalog references, S3 inputs, parameters, and resources are copied
        into the submitted contract before publishing. The worker therefore
        never needs a database connection or legacy trainer configuration.
        """
        settings = get_settings().training_code_runtime
        if not settings.enabled or not settings.base_url.strip() or not settings.execution_enabled:
            raise BadRequestException("custom training script execution is disabled")
        if data.input_mode == "script_managed" and not settings.allow_script_managed_data:
            raise BadRequestException("script-managed training data is disabled by platform policy")

        package = await db.scalar(
            select(TrainingRuntimeCodePackage).where(
                TrainingRuntimeCodePackage.id == data.code_package_id,
                TrainingRuntimeCodePackage.is_deleted == False,
                TrainingRuntimeCodePackage.enabled == True,
            )
        )
        if package is None:
            raise NotFoundException(f"training code package {data.code_package_id} not found")
        if package.runtime_id not in settings.execution_runtime_ids:
            raise BadRequestException(
                f"training runtime `{package.runtime_id}` is not enabled for execution"
            )
        declared_input_modes = self._load_json(package.input_modes_json, ["platform_dataset"])
        if data.input_mode not in declared_input_modes:
            raise BadRequestException(
                f"training code package {data.code_package_id} does not support `{data.input_mode}` input"
            )

        task_kind, default_annotation_kind = self._runtime_task_metadata(data.task_type)
        supported_tasks = self._load_json(package.supported_tasks_json, [])
        self._validate_runtime_parameters(
            self._load_json(package.parameters_schema_json, {}),
            data.parameters,
        )
        self._validate_runtime_package_task(
            supported_tasks=supported_tasks,
            task_kind=task_kind,
            data_modalities=data.data_modalities,
            annotation_kinds=(
                [default_annotation_kind] if data.input_mode == "platform_dataset" else data.annotation_kinds
            ),
        )

        resolved_sources: list[dict[str, Any]] = []
        snapshot = None
        if data.input_mode == "platform_dataset":
            resolved_sources = await self._resolve_and_validate_sources(
                db,
                data,
                include_annotation_content=False,
            )
            source_manifest = TrainingDatasetSnapshotManifest.model_validate(
                self._dataset_snapshot_builder.build(
                    task_type=data.task_type,
                    sources=resolved_sources,
                )
            )
            snapshot = await TrainingDatasetSnapshotRegistrar(
                base_url=settings.base_url,
                timeout=settings.timeout,
                token=settings.token,
            ).register(source_manifest, source_count=len(resolved_sources))
            class_names = snapshot.manifest.class_names
            data_modalities = snapshot.manifest.data_modalities
            annotation_kinds = snapshot.manifest.annotation_kinds
        else:
            class_names = self._normalize_runtime_class_names(data.class_names)
            data_modalities = self._normalize_runtime_strings(data.data_modalities, "data_modalities")
            annotation_kinds = self._normalize_runtime_strings(data.annotation_kinds, "annotation_kinds")

        model_input = await self._resolve_runtime_model_input(
            db,
            package=package,
            model_package_id=data.model_package_id,
            requested_mode=data.model_input_mode,
            task_kind=task_kind,
            class_names=class_names,
        )
        primary_source = resolved_sources[0] if resolved_sources else None
        execution_id = str(uuid4())
        task_config = {
            "training_backend": "model_training_runtime",
            "execution_id": execution_id,
            "code_package": {
                "id": package.id,
                "key": package.package_key,
                "version": package.version,
                "sha256": package.package_sha256,
            },
            "input_mode": data.input_mode,
            "parameters": data.parameters,
            "resources": data.resources.model_dump(mode="json"),
            "model_package_id": data.model_package_id,
            "model_input_mode": data.model_input_mode if model_input is not None else None,
        }
        task = await crud.create_task(
            db,
            task_type=data.task_type,
            dataset_id=primary_source["dataset_id"] if primary_source else None,
            annotation_id=primary_source["annotation_id"] if primary_source else None,
            config=json.dumps(task_config, ensure_ascii=False, sort_keys=True),
            status=TaskStatus.PENDING.value,
        )
        if resolved_sources:
            await crud.create_task_sources(
                db,
                task_id=task.id,
                sources=[
                    {
                        "dataset_id": source["dataset_id"],
                        "annotation_id": source["annotation_id"],
                        "source_order": source["source_order"],
                        "source_name": source["source_name"],
                    }
                    for source in resolved_sources
                ],
            )

        submission = {
            "protocol_version": "training-code-submit/v1",
            "message_id": str(uuid4()),
            "execution_id": execution_id,
            "task": {"task_id": task.id, "task_kind": task_kind},
            "package": {
                "key": package.package_key,
                "version": package.version,
                "sha256": package.package_sha256,
            },
            "package_archive": {
                "bucket": "default",
                "object_key": package.package_object_key,
                "sha256": package.package_sha256,
                "size_bytes": package.package_size_bytes,
            },
            "input_mode": data.input_mode,
            "runtime": {"id": package.runtime_id, "kind": "platform_managed"},
            "parameters": data.parameters,
            "resources": data.resources.model_dump(mode="json"),
        }
        if snapshot is not None:
            submission["dataset_source_snapshot"] = snapshot.object.model_dump(mode="json")
        else:
            submission["script_dataset"] = {
                "protocol_version": "training-dataset-manifest/v1",
                "task_kind": task_kind,
                "data_modalities": data_modalities,
                "annotation_kinds": annotation_kinds,
                "class_names": class_names,
                "items": [],
            }
        if model_input is not None:
            submission["model_input"] = model_input
        execution = TrainingRuntimeExecution(
            task_id=task.id,
            execution_id=execution_id,
            code_package_id=package.id,
            model_package_id=data.model_package_id,
            input_mode=data.input_mode,
            submission_json=json.dumps(submission, ensure_ascii=False, sort_keys=True),
            status="queued",
        )
        db.add(execution)
        await db.commit()
        await db.refresh(task)

        try:
            await asyncio.to_thread(self.publisher.publish_training_code_execution, submission)
            logger.info("Custom training task %s queued: execution_id=%s", task.id, execution_id)
        except Exception as exc:
            task.status = TaskStatus.FAILED.value
            task.error_message = str(exc)
            execution.status = "failed"
            execution.error_message = str(exc)
            db.add_all([task, execution])
            await db.commit()
            raise AppException(
                code=503,
                message=f"Failed to queue custom training task: {exc}",
                data=(await self._serialize_task(db, task)).model_dump(mode="json"),
            ) from exc

        return await self._serialize_task(db, task)

    async def get_task(self, db: AsyncSession, task_id: int) -> TaskResponse:
        task = await crud.get_task_by_id(db, task_id)
        if not task:
            raise NotFoundException(f"Task {task_id} not found")
        return await self._serialize_task(db, task)

    async def list_tasks(self, db: AsyncSession, page: int = 1, page_size: int = 10, status: int = None) -> tuple[List[TaskResponse], int]:
        offset = (page - 1) * page_size
        items, total = await crud.get_tasks(db, offset, page_size, status)
        sources_map = await crud.get_task_sources_by_task_ids(db, [item.id for item in items])
        serialized = [
            self._serialize_task_from_sources(item, sources_map.get(item.id, []))
            for item in items
        ]
        return serialized, total

    async def get_home_summary(self, db: AsyncSession) -> TaskSummaryResponse:
        total = (
            await db.execute(
                select(func.count()).select_from(Task).where(Task.is_deleted == False)
            )
        ).scalar() or 0
        running = (
            await db.execute(
                select(func.count()).select_from(Task).where(
                    Task.is_deleted == False,
                    Task.status == TaskStatus.RUNNING.value,
                )
            )
        ).scalar() or 0
        completed = (
            await db.execute(
                select(func.count()).select_from(Task).where(
                    Task.is_deleted == False,
                    Task.status == TaskStatus.COMPLETED.value,
                )
            )
        ).scalar() or 0
        return TaskSummaryResponse(
            total=int(total),
            running=int(running),
            completed=int(completed),
        )

    async def get_task_logs(self, db: AsyncSession, task_id: int, page: int = 1, page_size: int = 100) -> tuple[List[TaskLogResponse], int]:
        task = await crud.get_task_by_id(db, task_id)
        if not task:
            raise NotFoundException(f"Task {task_id} not found")

        offset = (page - 1) * page_size
        logs, total = await crud.get_task_logs(db, task_id, offset, page_size)
        return [TaskLogResponse.model_validate(log) for log in logs], total

    async def get_base_models(self, db: AsyncSession) -> List[BaseModelResponse]:
        models = await crud.get_base_models(db)
        return [BaseModelResponse.model_validate(m) for m in models]

    async def get_training_history_candidates(
        self,
        db: AsyncSession,
        data: TrainingHistoryQuery,
    ) -> List[TrainingHistoryCandidateResponse]:
        if data.task_type == TaskType.POSE:
            return []

        source_pairs = self._normalize_source_pairs(data.sources)
        if not source_pairs:
            return []

        model_types = self._resolve_history_model_types(
            task_type=data.task_type,
            label_format=data.label_format,
        )
        rows = await crud.get_training_history_candidates(
            db,
            task_type=data.task_type,
            source_pairs=source_pairs,
            model_types=model_types,
        )
        return [
            TrainingHistoryCandidateResponse(
                model_id=model.id,
                task_id=model.task_id or 0,
                model_name=model.name or model.model_path or "",
                model_path=model.model_path,
                model_type=model.model_type,
                base_model_name=self._extract_base_model_name(model.name),
                dataset_id=model.dataset_id,
                annotation_id=source_pairs[0][1] if source_pairs else None,
                source_count=int(source_count or 0),
                created_at=model.created_at,
            )
            for model, source_count in rows
            if model.task_id
        ]

    async def preview_training_dataset_snapshot(
        self,
        db: AsyncSession,
        data: TrainingDatasetSnapshotPreviewRequest,
    ) -> TrainingDatasetSnapshotPreviewResponse:
        """Build the future worker input manifest without writing or queuing anything."""
        if data.task_type == TaskType.POSE:
            raise BadRequestException("pose task is not supported yet")
        if data.task_type not in {TaskType.DETECTION, TaskType.CLASSIFICATION, TaskType.SEGMENTATION}:
            raise BadRequestException(f"unsupported task_type: {data.task_type}")
        manifest, source_count = await self._build_training_dataset_snapshot_manifest(
            db, data
        )
        return TrainingDatasetSnapshotPreviewResponse(
            manifest=manifest,
            source_count=source_count,
            sample_count=len(manifest.items),
            registration_enabled=self._training_code_runtime_registration_enabled(),
        )

    async def register_training_dataset_snapshot(
        self,
        db: AsyncSession,
        data: TrainingDatasetSnapshotRegisterRequest,
    ) -> TrainingDatasetSnapshotRegistrationResponse:
        """Pin source objects through the experimental runtime; never dispatch a task."""
        settings = get_settings().training_code_runtime
        if not settings.enabled or not settings.base_url.strip():
            raise BadRequestException("training code runtime dataset registration is disabled")
        manifest, source_count = await self._build_training_dataset_snapshot_manifest(db, data)
        registrar = TrainingDatasetSnapshotRegistrar(
            base_url=settings.base_url,
            timeout=settings.timeout,
            token=settings.token,
        )
        return await registrar.register(manifest, source_count=source_count)

    async def _build_training_dataset_snapshot_manifest(
        self,
        db: AsyncSession,
        data: TrainingDatasetSnapshotPreviewRequest,
    ) -> tuple[TrainingDatasetSnapshotManifest, int]:
        resolved_sources = await self._resolve_and_validate_sources(
            db,
            data,
            include_annotation_content=False,
        )
        manifest = TrainingDatasetSnapshotManifest.model_validate(
            self._dataset_snapshot_builder.build(
                task_type=data.task_type,
                sources=resolved_sources,
            )
        )
        return manifest, len(resolved_sources)

    @staticmethod
    def _runtime_task_metadata(task_type: int) -> tuple[str, str]:
        mapping = {
            TaskType.DETECTION: ("detection", "detection"),
            TaskType.CLASSIFICATION: ("classification", "classification"),
            TaskType.SEGMENTATION: ("segmentation", "segmentation"),
        }
        metadata = mapping.get(task_type)
        if metadata is None:
            raise BadRequestException(f"unsupported custom training task_type: {task_type}")
        return metadata

    @staticmethod
    def _load_json(value: str | None, fallback: Any) -> Any:
        if not value:
            return fallback
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return fallback

    @staticmethod
    def _normalize_runtime_strings(values: list[str], field_name: str) -> list[str]:
        normalized = [str(value).strip() for value in values]
        if not normalized or any(not value for value in normalized) or len(normalized) != len(set(normalized)):
            raise BadRequestException(f"{field_name} must contain unique non-empty values")
        return normalized

    def _normalize_runtime_class_names(self, values: list[str]) -> list[str]:
        return self._normalize_runtime_strings(values, "class_names")

    @staticmethod
    def _validate_runtime_package_task(
        *,
        supported_tasks: Any,
        task_kind: str,
        data_modalities: list[str],
        annotation_kinds: list[str],
    ) -> None:
        if not isinstance(supported_tasks, list):
            raise BadRequestException("training code package has invalid supported task metadata")
        for supported in supported_tasks:
            if not isinstance(supported, dict) or supported.get("task_kind") != task_kind:
                continue
            supported_modalities = supported.get("data_modalities")
            supported_annotations = supported.get("annotation_kinds")
            if (
                isinstance(supported_modalities, list)
                and isinstance(supported_annotations, list)
                and set(data_modalities).issubset(set(supported_modalities))
                and set(annotation_kinds).issubset(set(supported_annotations))
            ):
                return
        raise BadRequestException(
            "training code package does not support the selected task type, modalities, or annotations"
        )

    @staticmethod
    def _validate_runtime_parameters(schema: Any, parameters: dict[str, Any]) -> None:
        if not isinstance(schema, dict):
            raise BadRequestException("training code package has invalid parameter schema")
        try:
            validator = Draft202012Validator(schema)
        except SchemaError as exc:
            raise BadRequestException(f"training code package has invalid parameter schema: {exc.message}") from exc
        errors = sorted(validator.iter_errors(parameters), key=lambda error: list(error.absolute_path))
        if not errors:
            return
        error = errors[0]
        location = "$parameters"
        for part in error.absolute_path:
            location += f"[{part!r}]" if isinstance(part, int) else f".{part}"
        raise BadRequestException(f"parameters violate package schema at {location}: {error.message}")

    async def _resolve_runtime_model_input(
        self,
        db: AsyncSession,
        *,
        package: TrainingRuntimeCodePackage,
        model_package_id: int | None,
        requested_mode: str,
        task_kind: str,
        class_names: list[str],
    ) -> dict[str, Any] | None:
        contract = self._load_json(package.model_input_contract_json, None)
        if model_package_id is None:
            if isinstance(contract, dict) and contract.get("required") is True:
                raise BadRequestException("the selected training code package requires a model package")
            return None
        if not isinstance(contract, dict):
            raise BadRequestException("the selected training code package does not accept a model package")
        model_package = await db.scalar(
            select(TrainingRuntimeModelPackage).where(
                TrainingRuntimeModelPackage.id == model_package_id,
                TrainingRuntimeModelPackage.is_deleted == False,
                TrainingRuntimeModelPackage.enabled == True,
            )
        )
        if model_package is None:
            raise NotFoundException(f"training model package {model_package_id} not found")
        modes = contract.get("modes") if isinstance(contract.get("modes"), list) else []
        if requested_mode not in modes:
            raise BadRequestException("the selected training code package does not support this model input mode")
        framework = contract.get("framework") if isinstance(contract.get("framework"), dict) else {}
        if framework.get("id") != model_package.framework_id or framework.get("version") != model_package.framework_version:
            raise BadRequestException("model package framework does not match the training code package")
        allowed_formats = contract.get("formats") if isinstance(contract.get("formats"), list) else []
        if model_package.artifact_format not in allowed_formats:
            raise BadRequestException("model package format is not accepted by the training code package")
        if contract.get("require_matching_task_kind", True) and model_package.task_kind != task_kind:
            raise BadRequestException("model package task type does not match the custom training task")
        package_class_names = self._load_json(model_package.class_names_json, [])
        if requested_mode == "resume":
            if not model_package.resume_object_key or not model_package.resume_sha256 or model_package.resume_size_bytes is None:
                raise BadRequestException("selected model package does not provide a resumable checkpoint")
            if contract.get("require_matching_class_names_for_resume", True) and package_class_names != class_names:
                raise BadRequestException("resume checkpoint class names do not match this training task")
            object_reference = {
                "bucket": "models",
                "object_key": model_package.resume_object_key,
                "sha256": model_package.resume_sha256,
                "size_bytes": model_package.resume_size_bytes,
            }
            resume_supported = True
        else:
            object_reference = {
                "bucket": "models",
                "object_key": model_package.initialize_object_key,
                "sha256": model_package.initialize_sha256,
                "size_bytes": model_package.initialize_size_bytes,
            }
            resume_supported = False
        return {
            "mode": requested_mode,
            "artifact": {
                "source": "uploaded_model_package",
                "object": object_reference,
                "format": model_package.artifact_format,
                "task_kind": model_package.task_kind,
                "class_names": package_class_names,
                "display_name": model_package.name,
                "framework": {
                    "id": model_package.framework_id,
                    "version": model_package.framework_version,
                },
                "resume_supported": resume_supported,
                "metadata": self._load_json(model_package.metadata_json, {}),
            },
        }

    @staticmethod
    def _training_code_runtime_registration_enabled() -> bool:
        settings = get_settings().training_code_runtime
        return bool(settings.enabled and settings.base_url.strip())

    async def delete_task(self, db: AsyncSession, task_id: int) -> bool:
        task = await crud.get_task_by_id(db, task_id)
        if not task:
            raise NotFoundException(f"Task {task_id} not found")
        if task.status in {TaskStatus.PENDING.value, TaskStatus.RUNNING.value, TaskStatus.POST_PROCESS.value}:
            config = self._load_json(task.config, {})
            if config.get("training_backend") == "model_training_runtime":
                raise BadRequestException(
                    "custom training tasks cannot be deleted while running; cancellation is not available yet"
                )
            await self._cancel_trainer_task(task_id)
        deleted = await crud.delete_task(db, task_id)
        await db.commit()
        return deleted

    async def get_trainer_status(self) -> TrainerStatusResponse:
        try:
            client = await self._get_trainer_client()
            response = await client.get("/health")
            if response.status_code != 200:
                return TrainerStatusResponse(
                    reachable=False,
                    status="unreachable",
                    message=f"model_trainer returned {response.status_code}",
                )
            payload = response.json()
            return TrainerStatusResponse(
                reachable=True,
                status=payload.get("status", "unknown"),
                version=payload.get("version"),
                mq_connected=bool(payload.get("mq_connected", False)),
                max_concurrent=int(payload.get("max_concurrent", 0) or 0),
                active_tasks=int(payload.get("active_tasks", 0) or 0),
                queued_tasks=int(payload.get("queued_tasks", 0) or 0),
                available_devices=list(payload.get("available_devices") or ["cpu"]),
            )
        except Exception as e:
            logger.warning(f"Failed to fetch trainer status: {e}")
            return TrainerStatusResponse(
                reachable=False,
                status="unreachable",
                message=str(e),
            )

    async def _resolve_and_validate_sources(
        self,
        db: AsyncSession,
        data: TaskCreate,
        *,
        include_annotation_content: bool = True,
    ) -> list[dict[str, Any]]:
        raw_sources = data.sources or []
        if not raw_sources:
            if data.dataset_id is None or data.annotation_id is None:
                raise BadRequestException("dataset_id and annotation_id are required when sources is empty")
            raw_sources = [{
                "dataset_id": data.dataset_id,
                "annotation_id": data.annotation_id,
            }]

        resolved_sources: list[dict[str, Any]] = []
        normalized_classes: Optional[List[str]] = None
        expected_annotation_type = (
            AnnotationType.DETECTION
            if data.task_type == TaskType.DETECTION
            else AnnotationType.CLASSIFICATION
            if data.task_type == TaskType.CLASSIFICATION
            else AnnotationType.SEGMENTATION
        )

        for index, item in enumerate(raw_sources):
            dataset_id = item.dataset_id if hasattr(item, "dataset_id") else item["dataset_id"]
            annotation_id = item.annotation_id if hasattr(item, "annotation_id") else item["annotation_id"]

            dataset = await db.scalar(
                select(Dataset).where(
                    Dataset.id == dataset_id,
                    Dataset.is_deleted == False,
                )
            )
            if not dataset:
                raise NotFoundException(f"Dataset {dataset_id} not found")

            annotation = await db.scalar(
                select(Annotation).where(
                    Annotation.id == annotation_id,
                    Annotation.is_deleted == False,
                )
            )
            if not annotation:
                raise NotFoundException(f"Annotation {annotation_id} not found")

            if dataset.data_type != DataType.IMAGE:
                raise BadRequestException(f"training source dataset {dataset_id} must be an image dataset")
            if annotation.dataset_id and annotation.dataset_id != dataset_id:
                raise BadRequestException(
                    f"annotation {annotation_id} is bound to dataset {annotation.dataset_id}, not {dataset_id}"
                )
            if annotation.annotation_type != expected_annotation_type:
                raise BadRequestException(
                    f"annotation {annotation_id} type mismatch: expected {int(expected_annotation_type)}, got {annotation.annotation_type}"
                )

            classes = parse_annotation_classes(annotation.classes)
            if data.task_type in {TaskType.DETECTION, TaskType.CLASSIFICATION, TaskType.SEGMENTATION} and not classes:
                raise BadRequestException(f"annotation {annotation_id} classes is empty")
            if normalized_classes is None:
                normalized_classes = classes
            elif classes != normalized_classes:
                raise BadRequestException("all sources must share the same normalized classes")

            samples = await self._build_training_samples(
                db,
                dataset_id,
                annotation_id,
                include_annotation_content=include_annotation_content,
            )
            if not samples:
                raise BadRequestException(
                    f"training source dataset_id={dataset_id}, annotation_id={annotation_id} has no asset-backed annotated samples"
                )

            resolved_sources.append({
                "dataset_id": dataset_id,
                "annotation_id": annotation_id,
                "classes": classes,
                "source_order": index,
                "source_name": f"{dataset.name} / {annotation.name}",
                "samples": samples,
            })

        if not resolved_sources:
            raise BadRequestException("at least one training source is required")
        return resolved_sources

    async def _build_training_samples(
        self,
        db: AsyncSession,
        dataset_id: int,
        annotation_id: int,
        *,
        include_annotation_content: bool = True,
    ) -> list[dict[str, Any]]:
        sample_result = await db.execute(
            select(SampleItem)
            .where(
                SampleItem.dataset_id == dataset_id,
                SampleItem.is_deleted == False,
            )
            .order_by(SampleItem.sort_order.asc(), SampleItem.created_at.asc(), SampleItem.id.asc())
        )
        sample_items = list(sample_result.scalars().all())
        if not sample_items:
            return []

        record_result = await db.execute(
            select(AnnotationRecord).where(
                AnnotationRecord.annotation_id == annotation_id,
                AnnotationRecord.is_deleted == False,
            )
        )
        record_map = {
            record.sample_item_id: record
            for record in record_result.scalars().all()
        }
        asset_ids = sorted({
            int(item.asset_id)
            for item in sample_items
            if item.asset_id
        })
        asset_map: dict[int, Asset] = {}
        if asset_ids:
            asset_result = await db.execute(
                select(Asset).where(
                    Asset.id.in_(asset_ids),
                    Asset.is_deleted == False,
                )
            )
            asset_map = {asset.id: asset for asset in asset_result.scalars().all()}

        prepared_samples: list[tuple[SampleItem, AnnotationRecord, Asset]] = []
        for item in sample_items:
            record = record_map.get(item.id)
            if not record:
                continue
            asset = asset_map.get(item.asset_id) if item.asset_id else None
            if not asset or not asset.save_path:
                continue
            prepared_samples.append((item, record, asset))

        if not prepared_samples:
            return []

        if include_annotation_content:
            record_contents = await asyncio.gather(
                *(
                    self._load_record_content(record.annotation_type, record.content)
                    for _, record, _ in prepared_samples
                )
            )
        else:
            # Snapshot preview only needs persisted object keys, never bytes.
            record_contents = [{} for _ in prepared_samples]

        samples: list[dict[str, Any]] = []
        for (item, record, asset), content in zip(prepared_samples, record_contents):
            samples.append({
                "sample_item_id": item.id,
                "item_key": item.item_key,
                "item_type": item.item_type,
                "locator": self._load_json_object(item.locator),
                "payload": self._load_json_object(item.payload),
                "asset": {
                    "id": asset.id,
                    "asset_type": asset.asset_type,
                    "file_name": asset.file_name,
                    "save_path": asset.save_path,
                    "mime_type": asset.mime_type,
                    "size_bytes": asset.size_bytes,
                    "meta": self._load_json_object(asset.meta_json),
                },
                "annotation": {
                    "id": record.id,
                    "annotation_type": record.annotation_type,
                    "status": record.status,
                    # Existing trainer ignores this extra field; the snapshot
                    # preview uses it to preserve the actual annotations key.
                    "storage_path": record.content,
                    "content": content,
                },
            })
        return samples

    def _serialize_training_source(self, source: dict[str, Any]) -> dict[str, Any]:
        return {
            "dataset_id": source["dataset_id"],
            "annotation_id": source["annotation_id"],
            "source_order": source["source_order"],
            "source_name": source["source_name"],
            "samples": source["samples"],
        }

    def _load_json_object(self, raw_value: Any) -> Optional[dict[str, Any]]:
        if not raw_value:
            return None
        if isinstance(raw_value, dict):
            return raw_value
        try:
            parsed = json.loads(raw_value)
        except (TypeError, json.JSONDecodeError):
            return None
        return parsed if isinstance(parsed, dict) else None

    async def _load_record_content(
        self,
        annotation_type: int,
        content_path: Any,
    ) -> dict[str, Any]:
        if not is_annotation_record_storage_path(content_path):
            return {}
        try:
            payload = await self.s3.get_file(content_path, bucket_type="annotations")
        except Exception as e:
            logger.warning(f"Failed to load annotation record content from {content_path}: {e}")
            return {}
        return parse_annotation_record_payload(
            annotation_type,
            payload,
            source_path=content_path,
        )

    async def _cancel_trainer_task(self, task_id: int):
        try:
            client = await self._get_trainer_client()
            response = await client.post(f"/tasks/{task_id}/cancel")
            if response.status_code != 200:
                raise BadRequestException(
                    f"Failed to cancel trainer task {task_id}: {response.text}"
                )
            logger.info(f"Trainer task cancellation requested: task_id={task_id}")
        except BadRequestException:
            raise
        except Exception as e:
            logger.error(f"Failed to cancel trainer task {task_id}: {e}")
            raise BadRequestException(f"Trainer cancel unavailable: {e}")

    async def _attach_resume_model(
        self,
        db: AsyncSession,
        task_config: dict[str, Any],
        task_type: int,
    ) -> dict[str, Any]:
        resume_model_id = task_config.get("resume_model_id")
        if not resume_model_id:
            return task_config

        model = await db.scalar(
            select(AvailableModel).where(
                AvailableModel.id == int(resume_model_id),
                AvailableModel.is_deleted == False,
            )
        )
        if not model:
            raise BadRequestException(f"resume model {resume_model_id} not found")
        if not model.model_path:
            raise BadRequestException(f"resume model {resume_model_id} has no model_path")

        allowed_model_types = self._resolve_history_model_types(
            task_type=task_type,
            label_format=task_config.get("label_format"),
        )
        if allowed_model_types and model.model_type not in allowed_model_types:
            raise BadRequestException(
                f"resume model {resume_model_id} type mismatch: {model.model_type}"
            )

        next_config = dict(task_config)
        next_config["resume_model"] = {
            "model_id": model.id,
            "task_id": model.task_id,
            "model_name": model.name,
            "save_path": model.model_path,
            "model_type": model.model_type,
        }
        return next_config

    def _normalize_source_pairs(self, sources: list[Any]) -> list[tuple[int, int]]:
        pairs: list[tuple[int, int]] = []
        seen: set[tuple[int, int]] = set()
        for item in sources:
            dataset_id = item.dataset_id if hasattr(item, "dataset_id") else item.get("dataset_id")
            annotation_id = item.annotation_id if hasattr(item, "annotation_id") else item.get("annotation_id")
            if not dataset_id or not annotation_id:
                continue
            pair = (int(dataset_id), int(annotation_id))
            if pair in seen:
                continue
            seen.add(pair)
            pairs.append(pair)
        pairs.sort(key=lambda current: (current[0], current[1]))
        return pairs

    def _resolve_history_model_types(
        self,
        *,
        task_type: int,
        label_format: Optional[str],
    ) -> list[str]:
        if task_type == TaskType.CLASSIFICATION:
            return ["classification"]
        if task_type == TaskType.SEGMENTATION:
            return ["segmentation"]
        if task_type == TaskType.DETECTION:
            normalized = (label_format or "auto").strip().lower()
            if normalized == "obb":
                return ["detection_obb"]
            if normalized == "bbox":
                return ["detection", "detection_bbox"]
            return ["detection", "detection_bbox", "detection_obb"]
        return []

    def _extract_base_model_name(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        prefix = name.split("-task-", 1)[0]
        if "-detection_" in prefix:
            return prefix.rsplit("-detection_", 1)[0]
        if prefix.endswith("-classification"):
            return prefix[: -len("-classification")]
        if prefix.endswith("-segmentation"):
            return prefix[: -len("-segmentation")]
        return prefix or None

    async def _serialize_task(self, db: AsyncSession, task) -> TaskResponse:
        sources = await crud.get_task_sources(db, task.id)
        return self._serialize_task_from_sources(task, sources)

    def _serialize_task_from_sources(self, task, sources) -> TaskResponse:
        payload = TaskResponse.model_validate(task).model_dump()
        stale_seconds = self._calc_stale_seconds(task.status, task.updated_at)
        payload["stale_seconds"] = stale_seconds
        payload["is_stale"] = stale_seconds is not None
        payload["sources"] = [TaskSourceResponse.model_validate(source).model_dump() for source in sources]
        return TaskResponse(**payload)

    def _calc_stale_seconds(self, status: int, updated_at: Optional[datetime]) -> Optional[int]:
        if status not in STALE_TASK_STATUSES or updated_at is None:
            return None
        timeout = int(getattr(get_settings(), "task_stale_timeout_seconds", DEFAULT_STALE_TIMEOUT_SECONDS))
        now = datetime.now(updated_at.tzinfo) if updated_at.tzinfo else datetime.now()
        current = updated_at
        seconds = max(0, int((now - current).total_seconds()))
        return seconds if seconds >= timeout else None


async def get_task_service():
    service = TaskService()
    try:
        yield service
    finally:
        await service.close()
