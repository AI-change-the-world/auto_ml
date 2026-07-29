"""Dataset batch annotation orchestration.

The API service owns task state and annotation persistence. The sandbox only
receives immutable chunk payloads and publishes structured results back via MQ.
"""
from __future__ import annotations

import asyncio
import io
import json
import math
import re
import uuid
import zipfile
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from loguru import logger
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BadRequestException, NotFoundException
from app.config.settings import get_settings
from app.db.models import (
    Annotation,
    AnnotationRecord,
    AiPipelineBatchRun,
    AiPipelineBatchRunEvent,
    AiPipelineBatchRunItem,
    AiPipelineBatchBuiltinScriptSetting,
    AiPipelineBatchScript,
    Asset,
    Dataset,
    SampleItem,
)
from app.mq.publisher import get_publisher
from app.utils.annotation_classes import parse_annotation_classes
from app.utils.s3_delegate import get_s3_delegate

from .batch_schemas import (
    AiPipelineBatchRunCreate,
    AiPipelineBatchRunDetailResponse,
    AiPipelineBatchRunEventResponse,
    AiPipelineBatchRunIncrementalStatus,
    AiPipelineBatchRunItemResponse,
    AiPipelineBatchRunProgressPoint,
    AiPipelineBatchRunResponse,
    AiPipelineBatchScriptResponse,
    AiPipelineBatchScriptUpdate,
    AiPipelineBatchScriptManifest,
)
from .batch_scripts import get_batch_script, list_batch_scripts


TERMINAL_ITEM_STATUSES = {"succeeded", "failed", "skipped", "canceled"}
SCRIPT_ARCHIVE_MAX_BYTES = 100 * 1024 * 1024
SCRIPT_ARCHIVE_MAX_FILES = 512
SCRIPT_ARCHIVE_MAX_UNPACKED_BYTES = 512 * 1024 * 1024
SCRIPT_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
SECRET_VALUE_MARKER = "__pipeline_batch_secret__"


class BatchDispatchFailure(Exception):
    """A batch chunk could not be prepared or sent to the sandbox queue."""

    def __init__(
        self,
        stage: str,
        message: str,
        *,
        unpublished_chunk_keys: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.unpublished_chunk_keys = unpublished_chunk_keys or []


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
    async def list_scripts(
        self,
        db: AsyncSession,
        *,
        include_disabled: bool = False,
    ) -> list[AiPipelineBatchScriptResponse]:
        conditions = [AiPipelineBatchScript.is_deleted == False]
        if not include_disabled:
            conditions.append(AiPipelineBatchScript.enabled == True)
        custom_scripts = list(
            (
                await db.execute(
                    select(AiPipelineBatchScript)
                    .where(*conditions)
                    .order_by(AiPipelineBatchScript.created_at.desc(), AiPipelineBatchScript.id.desc())
                )
            ).scalars().all()
        )
        builtin_scripts = list_batch_scripts()
        builtin_enabled_by_key = await self._get_builtin_enabled_by_key(db, builtin_scripts)
        builtins = [
            self._to_script_response(
                self._builtin_script(item, enabled=builtin_enabled_by_key.get(item["key"], True))
            )
            for item in builtin_scripts
            if include_disabled or builtin_enabled_by_key.get(item["key"], True)
        ]
        return [*builtins, *(self._to_script_response(self._custom_script_dict(item)) for item in custom_scripts)]

    async def get_script(
        self,
        db: AsyncSession,
        script_key: str,
    ) -> AiPipelineBatchScriptResponse:
        script = await self._get_script(db, script_key)
        if not script:
            raise NotFoundException(f"Batch script {script_key} not found")
        return self._to_script_response(script)

    async def upload_script(
        self,
        db: AsyncSession,
        archive_name: str,
        archive_bytes: bytes,
    ) -> AiPipelineBatchScriptResponse:
        manifest = self._read_bundle_manifest(archive_bytes)
        if get_batch_script(manifest.key):
            raise BadRequestException("script key is reserved by a platform script")
        entrypoint = self._normalize_entrypoint(manifest.entrypoint)
        normalized_fields = self._normalize_parameter_fields(manifest.parameters)
        self._validate_script_archive(archive_bytes, entrypoint)

        archive_file_name = PurePosixPath(archive_name or "script.zip").name
        if not archive_file_name.lower().endswith(".zip"):
            raise BadRequestException("script package must be a .zip file")
        object_key = f"uploads/batch-scripts/{manifest.key}/{uuid.uuid4().hex}.zip"
        await get_s3_delegate().put_file(
            object_key,
            archive_bytes,
            bucket_type="default",
            content_type="application/zip",
        )

        script = await db.scalar(
            select(AiPipelineBatchScript).where(AiPipelineBatchScript.script_key == manifest.key)
        )
        if script is None:
            script = AiPipelineBatchScript(script_key=manifest.key)
            db.add(script)
        script.version = manifest.version.strip()
        script.name = manifest.name.strip()
        script.description = manifest.description.strip() if manifest.description else None
        script.package_object_key = object_key
        script.package_file_name = archive_file_name
        script.entrypoint = entrypoint
        script.supported_data_types_json = _dump_json(sorted(set(manifest.supported_data_types)))
        script.supported_annotation_types_json = _dump_json(sorted(set(manifest.supported_annotation_types)))
        script.parameter_fields_json = _dump_json(normalized_fields)
        script.enabled = True
        script.is_deleted = False
        await db.commit()
        await db.refresh(script)
        return self._to_script_response(self._custom_script_dict(script))

    async def update_script(
        self,
        db: AsyncSession,
        script_key: str,
        data: AiPipelineBatchScriptUpdate,
    ) -> AiPipelineBatchScriptResponse:
        update_data = data.model_dump(exclude_unset=True)
        builtin = get_batch_script(script_key)
        if builtin:
            setting = await db.scalar(
                select(AiPipelineBatchBuiltinScriptSetting).where(
                    AiPipelineBatchBuiltinScriptSetting.script_key == builtin["key"]
                )
            )
            if setting is None:
                setting = AiPipelineBatchBuiltinScriptSetting(script_key=builtin["key"])
                db.add(setting)
            if "enabled" in update_data:
                setting.enabled = bool(update_data["enabled"])
            await db.commit()
            await db.refresh(setting)
            return self._to_script_response(self._builtin_script(builtin, enabled=setting.enabled))

        script = await self._get_custom_script(db, script_key)
        if "enabled" in update_data:
            script.enabled = bool(update_data["enabled"])
        await db.commit()
        await db.refresh(script)
        return self._to_script_response(self._custom_script_dict(script))

    async def delete_script(self, db: AsyncSession, script_key: str) -> None:
        script = await self._get_custom_script(db, script_key)
        script.enabled = False
        script.is_deleted = True
        await db.commit()

    async def _get_script(self, db: AsyncSession, script_key: str) -> dict[str, Any] | None:
        builtin = get_batch_script(script_key)
        if builtin:
            setting = await db.scalar(
                select(AiPipelineBatchBuiltinScriptSetting).where(
                    AiPipelineBatchBuiltinScriptSetting.script_key == builtin["key"]
                )
            )
            if setting and not setting.enabled:
                return None
            return self._builtin_script(builtin, enabled=setting.enabled if setting else True)
        script = await db.scalar(
            select(AiPipelineBatchScript).where(
                AiPipelineBatchScript.script_key == script_key,
                AiPipelineBatchScript.is_deleted == False,
                AiPipelineBatchScript.enabled == True,
            )
        )
        return self._custom_script_dict(script) if script else None

    async def _get_custom_script(self, db: AsyncSession, script_key: str) -> AiPipelineBatchScript:
        script = await db.scalar(
            select(AiPipelineBatchScript).where(
                AiPipelineBatchScript.script_key == script_key,
                AiPipelineBatchScript.is_deleted == False,
            )
        )
        if not script:
            raise NotFoundException(f"Batch script {script_key} not found")
        return script

    @staticmethod
    def _builtin_script(script: dict[str, Any], *, enabled: bool = True) -> dict[str, Any]:
        return {
            **script,
            "entrypoint": f"{script['key']}.py",
            "package_object_key": None,
            "is_builtin": True,
            "enabled": enabled,
        }

    @staticmethod
    async def _get_builtin_enabled_by_key(
        db: AsyncSession,
        builtin_scripts: list[dict[str, Any]],
    ) -> dict[str, bool]:
        keys = [str(script["key"]) for script in builtin_scripts]
        if not keys:
            return {}
        settings = list(
            (
                await db.execute(
                    select(AiPipelineBatchBuiltinScriptSetting).where(
                        AiPipelineBatchBuiltinScriptSetting.script_key.in_(keys)
                    )
                )
            ).scalars().all()
        )
        return {setting.script_key: setting.enabled for setting in settings}

    @staticmethod
    def _custom_script_dict(script: AiPipelineBatchScript) -> dict[str, Any]:
        return {
            "key": script.script_key,
            "version": script.version,
            "name": script.name,
            "description": script.description,
            "supported_data_types": _load_json(script.supported_data_types_json, []),
            "supported_annotation_types": _load_json(script.supported_annotation_types_json, []),
            "parameter_fields": _load_json(script.parameter_fields_json, []),
            "entrypoint": script.entrypoint,
            "package_object_key": script.package_object_key,
            "is_builtin": False,
            "enabled": script.enabled,
        }

    @staticmethod
    def _to_script_response(script: dict[str, Any]) -> AiPipelineBatchScriptResponse:
        return AiPipelineBatchScriptResponse(
            key=str(script["key"]),
            version=str(script["version"]),
            name=str(script["name"]),
            description=script.get("description"),
            supported_data_types=list(script.get("supported_data_types") or []),
            supported_annotation_types=list(script.get("supported_annotation_types") or []),
            parameter_fields=list(script.get("parameter_fields") or []),
            entrypoint=script.get("entrypoint"),
            is_builtin=bool(script.get("is_builtin")),
            enabled=bool(script.get("enabled", True)),
        )

    @staticmethod
    def _normalize_entrypoint(value: str) -> str:
        entrypoint = str(value or "").strip().replace("\\", "/")
        path = PurePosixPath(entrypoint)
        if not entrypoint.endswith(".py") or path.is_absolute() or ".." in path.parts or entrypoint.startswith("./"):
            raise BadRequestException("entrypoint must be a relative .py path inside the ZIP package")
        return path.as_posix()

    @staticmethod
    def _validate_script_archive(archive_bytes: bytes, entrypoint: str) -> None:
        if not archive_bytes:
            raise BadRequestException("script package is empty")
        if len(archive_bytes) > SCRIPT_ARCHIVE_MAX_BYTES:
            raise BadRequestException("script package exceeds the 100 MB upload limit")
        try:
            archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
        except zipfile.BadZipFile as exc:
            raise BadRequestException("script package must be a valid ZIP archive") from exc
        with archive:
            infos = archive.infolist()
            if len(infos) > SCRIPT_ARCHIVE_MAX_FILES:
                raise BadRequestException("script package contains too many files")
            total_size = 0
            found_entrypoint = False
            for info in infos:
                path = PurePosixPath(info.filename)
                mode = info.external_attr >> 16
                if path.is_absolute() or ".." in path.parts or info.filename.startswith("/") or (mode & 0o170000) == 0o120000:
                    raise BadRequestException("script package contains an unsafe file path")
                if info.is_dir():
                    continue
                total_size += info.file_size
                if total_size > SCRIPT_ARCHIVE_MAX_UNPACKED_BYTES:
                    raise BadRequestException("script package is too large after extraction")
                if path.as_posix() == entrypoint:
                    found_entrypoint = True
            if not found_entrypoint:
                raise BadRequestException("entrypoint file does not exist in the ZIP package")

    @staticmethod
    def _read_bundle_manifest(archive_bytes: bytes) -> AiPipelineBatchScriptManifest:
        try:
            archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
        except zipfile.BadZipFile as exc:
            raise BadRequestException("script package must be a valid ZIP archive") from exc
        with archive:
            manifest_entries = [
                info for info in archive.infolist()
                if not info.is_dir() and PurePosixPath(info.filename).as_posix() == "batch_script.json"
            ]
            if len(manifest_entries) != 1:
                raise BadRequestException("script ZIP must contain exactly one root batch_script.json manifest")
            manifest_entry = manifest_entries[0]
            if manifest_entry.file_size > 256 * 1024:
                raise BadRequestException("batch_script.json exceeds the 256 KB limit")
            try:
                manifest_payload = json.loads(archive.read(manifest_entry).decode("utf-8"))
                return AiPipelineBatchScriptManifest.model_validate(manifest_payload)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
                raise BadRequestException(f"invalid batch_script.json manifest: {exc}") from exc

    @staticmethod
    def _normalize_parameter_fields(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        keys: set[str] = set()
        for raw_field in fields:
            if not isinstance(raw_field, dict):
                raise BadRequestException("parameter fields must be objects")
            key = str(raw_field.get("key") or "").strip()
            if not SCRIPT_KEY_PATTERN.fullmatch(key) or key in keys:
                raise BadRequestException("parameter field keys must be unique lowercase identifiers")
            value_type = str(raw_field.get("value_type") or "string").strip().lower()
            if value_type not in {"string", "number", "boolean", "select", "secret"}:
                raise BadRequestException("parameter value_type must be string, number, boolean, select, or secret")
            options = raw_field.get("options")
            if value_type == "select":
                if not isinstance(options, list) or not options:
                    raise BadRequestException("select parameters require at least one option")
                if any(not isinstance(option, (str, int, float)) or isinstance(option, bool) for option in options):
                    raise BadRequestException("select parameter options must be strings or numbers")
            widget = str(raw_field.get("widget") or "").strip().lower()
            if widget and widget not in {"number", "textarea"}:
                raise BadRequestException("parameter widget must be number or textarea")
            value_source = str(raw_field.get("value_source") or "").strip().lower()
            if value_source and value_source != "annotation_classes":
                raise BadRequestException("parameter value_source must be annotation_classes")
            if value_source and value_type != "string":
                raise BadRequestException("annotation_classes value_source requires a string parameter")
            normalized_field = {
                "key": key,
                "label": str(raw_field.get("label") or key).strip()[:128],
                "value_type": value_type,
                "required": bool(raw_field.get("required", False)),
                "default_value": raw_field.get("default_value"),
                "description": str(raw_field.get("description") or "").strip()[:500] or None,
            }
            if options is not None:
                normalized_field["options"] = options
            if widget:
                normalized_field["widget"] = widget
            if value_source:
                normalized_field["value_source"] = value_source
            if value_type == "secret" and normalized_field["default_value"] is not None:
                raise BadRequestException("secret parameters cannot define a default value")
            if normalized_field["default_value"] is not None:
                BatchAnnotationService._validate_parameter_value(normalized_field, normalized_field["default_value"])
            normalized.append(normalized_field)
            keys.add(key)
        return normalized

    @staticmethod
    def _validate_parameter_value(field: dict[str, Any], value: Any) -> None:
        value_type = field.get("value_type")
        if value_type == "string" and not isinstance(value, str):
            raise BadRequestException(f"parameter `{field['key']}` must be a string")
        if value_type == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
            raise BadRequestException(f"parameter `{field['key']}` must be a number")
        if value_type == "boolean" and not isinstance(value, bool):
            raise BadRequestException(f"parameter `{field['key']}` must be a boolean")
        if value_type == "select" and value not in (field.get("options") or []):
            raise BadRequestException(f"parameter `{field['key']}` has an unsupported value")
        if value_type == "secret" and not isinstance(value, str):
            raise BadRequestException(f"parameter `{field['key']}` must be a string")

    def _resolve_script_params(
        self,
        script: dict[str, Any],
        params: dict[str, Any],
        *,
        annotation_classes: list[str] | None = None,
    ) -> dict[str, Any]:
        fields = self._normalize_parameter_fields(list(script.get("parameter_fields") or []))
        field_by_key = {field["key"]: field for field in fields}
        unexpected = sorted(set(params) - set(field_by_key))
        if unexpected:
            raise BadRequestException(f"unsupported script parameters: {', '.join(unexpected)}")
        resolved: dict[str, Any] = {}
        for field in fields:
            key = field["key"]
            if field.get("value_source") == "annotation_classes" and annotation_classes:
                value = ", ".join(annotation_classes)
            else:
                value = params.get(key, field.get("default_value"))
            if value is None:
                if field["required"]:
                    raise BadRequestException(f"script parameter `{key}` is required")
                continue
            if field["required"] and isinstance(value, str) and not value.strip():
                raise BadRequestException(f"script parameter `{key}` cannot be blank")
            self._validate_parameter_value(field, value)
            resolved[key] = value
        return resolved

    @staticmethod
    def _get_secret_cipher() -> Fernet:
        key = get_settings().pipeline_batch_secret_key.strip()
        if not key:
            raise BadRequestException(
                "批量标注密钥未配置，请设置 Nacos ai-pipeline-batch.secret_key"
            )
        try:
            return Fernet(key.encode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise BadRequestException("批量标注密钥必须是有效的 Fernet key") from exc

    def _protect_script_params(self, script: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        field_by_key = {
            field["key"]: field
            for field in self._normalize_parameter_fields(list(script.get("parameter_fields") or []))
        }
        protected: dict[str, Any] = {}
        cipher: Fernet | None = None
        for key, value in params.items():
            if field_by_key[key].get("value_type") != "secret":
                protected[key] = value
                continue
            cipher = cipher or self._get_secret_cipher()
            protected[key] = {
                SECRET_VALUE_MARKER: cipher.encrypt(value.encode("utf-8")).decode("utf-8"),
            }
        return protected

    def _reveal_script_params(self, stored_params: dict[str, Any]) -> dict[str, Any]:
        revealed: dict[str, Any] = {}
        cipher: Fernet | None = None
        for key, value in stored_params.items():
            if not isinstance(value, dict) or not isinstance(value.get(SECRET_VALUE_MARKER), str):
                revealed[key] = value
                continue
            cipher = cipher or self._get_secret_cipher()
            try:
                revealed[key] = cipher.decrypt(value[SECRET_VALUE_MARKER].encode("utf-8")).decode("utf-8")
            except InvalidToken as exc:
                raise BadRequestException(
                    "stored batch secret cannot be decrypted with Nacos ai-pipeline-batch.secret_key"
                ) from exc
        return revealed

    @staticmethod
    def _mask_script_params(stored_params: dict[str, Any]) -> dict[str, Any]:
        return {
            key: "******" if isinstance(value, dict) and SECRET_VALUE_MARKER in value else value
            for key, value in stored_params.items()
        }

    async def create_run(
        self,
        db: AsyncSession,
        data: AiPipelineBatchRunCreate,
        *,
        batch_group_id: str | None = None,
    ) -> AiPipelineBatchRunResponse:
        script = await self._get_script(db, data.script_key)
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
        script_params = self._resolve_script_params(
            script,
            data.script_params,
            annotation_classes=parse_annotation_classes(annotation.classes),
        )
        protected_script_params = self._protect_script_params(script, script_params)

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
            batch_group_id=batch_group_id or f"batch_group_{uuid.uuid4().hex}",
            dataset_id=dataset.id,
            annotation_id=annotation.id,
            script_key=script["key"],
            script_version=script["version"],
            script_package_path=script.get("package_object_key"),
            script_entrypoint=script.get("entrypoint"),
            status="queued",
            selection_mode=data.selection_mode,
            overwrite_policy=data.overwrite_policy,
            batch_size=data.batch_size,
            parallelism=data.parallelism,
            total_count=len(samples),
            script_params_json=_dump_json(protected_script_params),
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
        event = await self._append_event(
            db,
            run.id,
            "queued",
            {"message": "batch run created", "total_count": run.total_count, "skipped_count": skipped_count},
        )
        await db.commit()
        await db.refresh(run)
        await self._publish_run_update(run, event)
        await self._dispatch_or_record_failure(db, run)
        return self._to_run_response(run)

    async def get_incremental_status(
        self,
        db: AsyncSession,
        run_id: str,
    ) -> AiPipelineBatchRunIncrementalStatus:
        source_run = await self._get_run(db, run_id)
        sample_ids = await self._get_incremental_sample_ids(db, source_run)
        return AiPipelineBatchRunIncrementalStatus(incremental_count=len(sample_ids))

    async def create_incremental_run(
        self,
        db: AsyncSession,
        run_id: str,
    ) -> AiPipelineBatchRunResponse:
        source_run = await self._get_run(db, run_id)
        if source_run.status in {"queued", "running"}:
            raise BadRequestException("wait for the current batch run to finish before processing new samples")
        if not source_run.batch_group_id:
            source_run.batch_group_id = f"batch_group_{source_run.run_id}"
            await db.flush()

        sample_ids = await self._get_incremental_sample_ids(db, source_run)
        if not sample_ids:
            raise BadRequestException("no new unannotated samples found")
        script_params = self._reveal_script_params(_load_json(source_run.script_params_json, {}))
        return await self.create_run(
            db,
            AiPipelineBatchRunCreate(
                dataset_id=source_run.dataset_id,
                annotation_id=source_run.annotation_id,
                script_key=source_run.script_key,
                selection_mode="selected",
                sample_item_ids=sample_ids,
                overwrite_policy=source_run.overwrite_policy,
                script_params=script_params,
                batch_size=source_run.batch_size,
                parallelism=source_run.parallelism,
            ),
            batch_group_id=source_run.batch_group_id,
        )

    async def _get_incremental_sample_ids(
        self,
        db: AsyncSession,
        source_run: AiPipelineBatchRun,
    ) -> list[int]:
        handled_samples = (
            select(AiPipelineBatchRunItem.id)
            .join(AiPipelineBatchRun, AiPipelineBatchRun.id == AiPipelineBatchRunItem.batch_run_id)
            .where(AiPipelineBatchRunItem.sample_item_id == SampleItem.id)
        )
        if source_run.batch_group_id:
            handled_samples = handled_samples.where(
                AiPipelineBatchRun.batch_group_id == source_run.batch_group_id
            )
        else:
            handled_samples = handled_samples.where(AiPipelineBatchRun.id == source_run.id)
        sample_ids = list(
            (
                await db.execute(
                    select(SampleItem.id)
                    .where(
                        SampleItem.dataset_id == source_run.dataset_id,
                        SampleItem.is_deleted == False,
                        ~handled_samples.exists(),
                    )
                    .order_by(SampleItem.id.asc())
                )
            ).scalars().all()
        )
        existing_records = await self._load_existing_records(
            db,
            source_run.annotation_id,
            sample_ids,
        )
        return [sample_id for sample_id in sample_ids if sample_id not in existing_records]

    async def list_runs(
        self,
        db: AsyncSession,
        *,
        dataset_id: int | None = None,
        annotation_id: int | None = None,
        script_key: str | None = None,
        limit: int = 50,
    ) -> list[AiPipelineBatchRunResponse]:
        conditions = [AiPipelineBatchRun.is_deleted == False]
        if dataset_id:
            conditions.append(AiPipelineBatchRun.dataset_id == dataset_id)
        if annotation_id:
            conditions.append(AiPipelineBatchRun.annotation_id == annotation_id)
        if script_key:
            conditions.append(AiPipelineBatchRun.script_key == script_key)
        stmt = (
            select(AiPipelineBatchRun)
            .where(*conditions)
            .order_by(AiPipelineBatchRun.created_at.desc(), AiPipelineBatchRun.id.desc())
            .limit(limit)
        )
        runs = list((await db.execute(stmt)).scalars().all())
        for run in runs:
            await self._reconcile_terminal_run_counts(db, run)
        return [self._to_run_response(item) for item in runs]

    async def get_run(self, db: AsyncSession, run_id: str) -> AiPipelineBatchRunDetailResponse:
        run = await self._get_run(db, run_id)
        await self._reconcile_terminal_run_counts(db, run)
        dataset = await db.scalar(
            select(Dataset).where(Dataset.id == run.dataset_id, Dataset.is_deleted == False)
        )
        annotation = await db.scalar(
            select(Annotation).where(Annotation.id == run.annotation_id, Annotation.is_deleted == False)
        )
        builtin_script = get_batch_script(run.script_key)
        custom_script = None
        if not builtin_script:
            custom_script = await db.scalar(
                select(AiPipelineBatchScript).where(AiPipelineBatchScript.script_key == run.script_key)
            )
        return AiPipelineBatchRunDetailResponse(
            **self._to_run_response(run).model_dump(),
            dataset_name=dataset.name if dataset else f"数据集 #{run.dataset_id}",
            annotation_name=annotation.name if annotation else f"标注项目 #{run.annotation_id}",
            script_name=str((builtin_script or {}).get("name") or getattr(custom_script, "name", None) or run.script_key),
            script_description=(builtin_script or {}).get("description") or getattr(custom_script, "description", None),
            progress_points=await self._get_run_progress_points(db, run),
        )

    async def list_items(
        self,
        db: AsyncSession,
        run_id: str,
        *,
        status: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[AiPipelineBatchRunItemResponse], int]:
        run = await self._get_run(db, run_id)
        conditions = [
            AiPipelineBatchRunItem.batch_run_id == run.id,
            AiPipelineBatchRunItem.is_deleted == False,
        ]
        if status == "pending":
            conditions.append(AiPipelineBatchRunItem.status.in_(["pending", "queued", "running"]))
        elif status:
            conditions.append(AiPipelineBatchRunItem.status == status)
        normalized_keyword = (keyword or "").strip()
        if normalized_keyword:
            conditions.append(AiPipelineBatchRunItem.item_key.like(f"%{normalized_keyword}%"))
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
        latest: bool = False,
    ) -> list[AiPipelineBatchRunEventResponse]:
        run = await self._get_run(db, run_id)
        latest_page = latest
        stmt = (
            select(AiPipelineBatchRunEvent)
            .where(
                AiPipelineBatchRunEvent.batch_run_id == run.id,
                AiPipelineBatchRunEvent.id > after_id,
                AiPipelineBatchRunEvent.is_deleted == False,
            )
            .order_by(AiPipelineBatchRunEvent.id.desc() if latest_page else AiPipelineBatchRunEvent.id.asc())
            .limit(limit)
        )
        events = list((await db.execute(stmt)).scalars().all())
        if latest_page:
            events.reverse()
        return [self._to_event_response(event) for event in events]

    async def _get_run_progress_points(
        self,
        db: AsyncSession,
        run: AiPipelineBatchRun,
    ) -> list[AiPipelineBatchRunProgressPoint]:
        events = list(
            (
                await db.execute(
                    select(AiPipelineBatchRunEvent)
                    .where(
                        AiPipelineBatchRunEvent.batch_run_id == run.id,
                        AiPipelineBatchRunEvent.event_type.in_(["progress", "result", "resumed"]),
                        AiPipelineBatchRunEvent.is_deleted == False,
                    )
                    .order_by(AiPipelineBatchRunEvent.id.desc())
                    .limit(240)
                )
            ).scalars().all()
        )
        events.reverse()
        points: list[AiPipelineBatchRunProgressPoint] = []
        for event in events:
            payload = _load_json(event.event_payload, {})
            if not isinstance(payload, dict) or event.created_at is None:
                continue
            if event.event_type == "resumed":
                if not points or points[-1].progress != 0:
                    points.append(AiPipelineBatchRunProgressPoint(progress=0, created_at=event.created_at))
                continue
            if event.event_type == "progress" and not self._is_execution_progress_event(payload):
                continue
            raw_progress = payload.get("run_progress", payload.get("progress"))
            if not isinstance(raw_progress, (int, float)) or isinstance(raw_progress, bool):
                continue
            progress = min(max(int(raw_progress), 0), 100)
            if event.event_type == "result" and points and progress < points[-1].progress:
                continue
            if points and points[-1].progress == progress:
                continue
            points.append(AiPipelineBatchRunProgressPoint(progress=progress, created_at=event.created_at))
        baseline_at = run.started_at or run.created_at
        if baseline_at is not None and len(events) < 240 and (not points or points[0].progress > 0):
            points.insert(0, AiPipelineBatchRunProgressPoint(progress=0, created_at=baseline_at))
        latest_at = run.finished_at or run.updated_at
        if latest_at is not None and (not points or points[-1].progress != run.progress):
            points.append(AiPipelineBatchRunProgressPoint(progress=run.progress, created_at=latest_at))
        return points

    @staticmethod
    def _is_execution_progress_event(payload: dict[str, Any]) -> bool:
        phase = payload.get("phase")
        if isinstance(phase, str):
            return phase == "execution"
        message = str(payload.get("message") or "")
        return message not in {
            "sandbox started",
            "sample input prepared",
            "preparing script virtual environment",
        } and not message.startswith("reuse_venv:")

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
                        AiPipelineBatchRunItem.status.in_(["pending", "queued", "running"]),
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
        event = await self._append_event(db, run.id, "canceled", {"message": "canceled by user"})
        await db.commit()
        await db.refresh(run)
        await self._publish_run_update(run, event)
        return self._to_run_response(run)

    async def delete_run(self, db: AsyncSession, run_id: str) -> None:
        run = await self._get_run(db, run_id)
        if run.status in {"queued", "running"}:
            raise BadRequestException("cancel an active batch run before deleting it")
        run.is_deleted = True
        await db.execute(
            update(AiPipelineBatchRunItem)
            .where(AiPipelineBatchRunItem.batch_run_id == run.id)
            .values(is_deleted=True)
        )
        await db.execute(
            update(AiPipelineBatchRunEvent)
            .where(AiPipelineBatchRunEvent.batch_run_id == run.id)
            .values(is_deleted=True)
        )
        await db.commit()

    async def resume_run(self, db: AsyncSession, run_id: str) -> AiPipelineBatchRunResponse:
        run = await self._get_run(db, run_id)
        if run.cancel_requested:
            raise BadRequestException("canceled batch runs cannot be resumed")

        if run.status == "queued":
            retryable_statuses = ["queued"]
        elif run.status in {"failed", "succeeded"}:
            retryable_statuses = ["failed", "pending"]
        else:
            raise BadRequestException("only queued or completed batch runs can be resumed")
        retryable_items = list(
            (
                await db.execute(
                    select(AiPipelineBatchRunItem).where(
                        AiPipelineBatchRunItem.batch_run_id == run.id,
                        AiPipelineBatchRunItem.status.in_(retryable_statuses),
                        AiPipelineBatchRunItem.is_deleted == False,
                    )
                )
            ).scalars().all()
        )
        if not retryable_items:
            raise BadRequestException("no retryable batch items found")

        for item in retryable_items:
            item.status = "pending"
            item.chunk_key = None
            item.started_at = None
            item.finished_at = None
            item.error_message = None
            item.result_json = None

        run.status = "queued"
        run.finished_at = None
        run.error_message = None
        await self._refresh_run_counts(db, run)

        event = await self._append_event(
            db,
            run.id,
            "resumed",
            {
                "requeued_count": len(retryable_items),
                "message": "failed items re-dispatched" if retryable_statuses == ["failed"] else "batch run re-dispatched",
            },
        )
        await db.commit()
        await db.refresh(run)
        await self._publish_run_update(run, event)
        await self._dispatch_or_record_failure(db, run)
        return self._to_run_response(run)

    async def handle_worker_progress(self, db: AsyncSession, payload: dict[str, Any]) -> None:
        run = await self._find_run(db, str(payload.get("run_id") or ""))
        if not run or run.cancel_requested:
            return
        chunk_key = str(payload.get("chunk_key") or "")
        if not chunk_key:
            return
        phase = str(payload.get("phase") or "execution")
        active_chunk_count = int(
            (
                await db.execute(
                    select(func.count()).select_from(AiPipelineBatchRunItem).where(
                        AiPipelineBatchRunItem.batch_run_id == run.id,
                        AiPipelineBatchRunItem.chunk_key == chunk_key,
                        AiPipelineBatchRunItem.status.in_(["queued", "running"]),
                        AiPipelineBatchRunItem.is_deleted == False,
                    )
                )
            ).scalar() or 0
        )
        if active_chunk_count == 0:
            return
        if run.status == "queued":
            run.status = "running"
            run.started_at = run.started_at or datetime.now()
        batch_item_id = payload.get("batch_item_id")
        if phase == "execution" and isinstance(batch_item_id, int) and not isinstance(batch_item_id, bool):
            item = await db.scalar(
                select(AiPipelineBatchRunItem).where(
                    AiPipelineBatchRunItem.id == batch_item_id,
                    AiPipelineBatchRunItem.batch_run_id == run.id,
                    AiPipelineBatchRunItem.chunk_key == chunk_key,
                    AiPipelineBatchRunItem.status == "queued",
                    AiPipelineBatchRunItem.is_deleted == False,
                )
            )
            if item:
                item.status = "running"
        terminal_stmt = select(func.count()).select_from(AiPipelineBatchRunItem).where(
            AiPipelineBatchRunItem.batch_run_id == run.id,
            AiPipelineBatchRunItem.status.in_(TERMINAL_ITEM_STATUSES),
            AiPipelineBatchRunItem.is_deleted == False,
        )
        completed_count = int((await db.execute(terminal_stmt)).scalar() or 0)
        current_chunk_progress = 0
        if phase == "execution":
            current_chunk_progress = min(
                max(int(payload.get("processed") or 0), 0),
                max(int(payload.get("total") or 0), 0),
            )
        run.progress = max(
            run.progress,
            self._calculate_progress(run.total_count, completed_count + current_chunk_progress),
        )
        event = await self._append_event(
            db,
            run.id,
            "progress",
            {
                "chunk_key": chunk_key,
                "processed": payload.get("processed"),
                "total": payload.get("total"),
                "run_progress": run.progress,
                "message": payload.get("message"),
                "phase": phase,
                "batch_item_id": batch_item_id,
            },
        )
        await db.commit()
        await db.refresh(run)
        await self._publish_run_update(run, event)

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
                        AiPipelineBatchRunItem.status.in_(["queued", "running"]),
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
                if item.status in {"queued", "running"}:
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
        event = await self._append_event(
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
        await self._publish_run_update(run, event)
        if run.status not in {"succeeded", "failed", "canceled"}:
            await self._dispatch_or_record_failure(db, run)

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
            result["error_detail"] = {
                "source": "automl_server",
                "stage": "validate_annotation_result",
                "message": item.error_message,
            }
            item.result_json = _dump_json(result)
            return
        try:
            from app.modules.annotation.schemas import AnnotationRecordSave
            from app.modules.annotation.service import AnnotationService

            annotation_service = AnnotationService()
            try:
                record = await annotation_service.save_annotation_record(
                    db,
                    run.annotation_id,
                    AnnotationRecordSave(sample_item_id=item.sample_item_id, content=content, status="saved"),
                )
            finally:
                await annotation_service.close()
        except Exception as exc:
            item.status = "failed"
            item.error_message = f"failed to save annotation result: {exc}"
            result["error_detail"] = {
                "source": "automl_server",
                "stage": "save_annotation_record",
                "exception_type": exc.__class__.__name__,
                "message": str(exc),
            }
            item.result_json = _dump_json(result)
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
                AiPipelineBatchRunItem.status.in_(["queued", "running"]),
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

        try:
            annotation_snapshot = _load_json(run.annotation_snapshot_json, {})
            script_params = self._reveal_script_params(_load_json(run.script_params_json, {}))
        except Exception as exc:
            raise BatchDispatchFailure("prepare_execute_payload", str(exc)) from exc

        chunks: list[tuple[str, list[AiPipelineBatchRunItem], dict[str, Any]]] = []
        for index in range(0, len(pending_items), run.batch_size):
            chunk_items = pending_items[index:index + run.batch_size]
            chunk_key = f"{run.run_id}_{uuid.uuid4().hex[:12]}"
            message = {
                "message_type": "pipeline.batch.execute",
                "service_name": "automl_server",
                "run_id": run.run_id,
                "chunk_key": chunk_key,
                "script_key": run.script_key,
                "script_version": run.script_version,
                "script_package_path": run.script_package_path,
                "script_entrypoint": run.script_entrypoint,
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
            for item in chunk_items:
                item.status = "queued"
                item.chunk_key = chunk_key
                item.attempt_count += 1
                item.started_at = item.started_at or datetime.now()
            chunks.append((chunk_key, chunk_items, message))
        await db.commit()

        for index, (chunk_key, _chunk_items, message) in enumerate(chunks):
            try:
                await asyncio.to_thread(get_publisher().publish_pipeline_batch_execute, message)
            except Exception as exc:
                unpublished_chunk_keys = [chunk[0] for chunk in chunks[index:]]
                raise BatchDispatchFailure(
                    "publish_execute_chunk",
                    "failed to publish batch chunk to RabbitMQ",
                    unpublished_chunk_keys=unpublished_chunk_keys,
                ) from exc

    async def _dispatch_or_record_failure(self, db: AsyncSession, run: AiPipelineBatchRun) -> None:
        try:
            await self._dispatch_available_chunks(db, run)
        except BatchDispatchFailure as exc:
            logger.exception(f"Batch dispatch failed: run_id={run.run_id} stage={exc.stage}")
            await self._record_dispatch_failure(db, run, exc)
        except Exception:
            logger.exception(f"Unexpected batch dispatch failure: run_id={run.run_id}")
            await db.rollback()
            run = await self._get_run(db, run.run_id)
            await self._record_dispatch_failure(
                db,
                run,
                BatchDispatchFailure(
                    "dispatch_available_chunks",
                    "unexpected server error while dispatching batch items",
                ),
            )

    async def _record_dispatch_failure(
        self,
        db: AsyncSession,
        run: AiPipelineBatchRun,
        failure: BatchDispatchFailure,
    ) -> None:
        now = datetime.now()
        conditions = [
            AiPipelineBatchRunItem.batch_run_id == run.id,
            AiPipelineBatchRunItem.is_deleted == False,
        ]
        if failure.unpublished_chunk_keys:
            conditions.append(
                (AiPipelineBatchRunItem.status == "pending")
                | (
                    (AiPipelineBatchRunItem.status == "queued")
                    & AiPipelineBatchRunItem.chunk_key.in_(failure.unpublished_chunk_keys)
                )
            )
        else:
            conditions.append(AiPipelineBatchRunItem.status == "pending")
        failed_items = list((await db.execute(select(AiPipelineBatchRunItem).where(*conditions))).scalars().all())
        error_detail = {
            "source": "automl_server",
            "stage": failure.stage,
            "exception_type": failure.__cause__.__class__.__name__ if failure.__cause__ else None,
            "message": str(failure),
        }
        for item in failed_items:
            item.status = "failed"
            item.chunk_key = None
            item.finished_at = now
            item.error_message = str(failure)
            item.result_json = _dump_json({"error_detail": error_detail})

        run.error_message = str(failure)
        await self._refresh_run_counts(db, run)
        event = await self._append_event(
            db,
            run.id,
            "dispatch_failed",
            {
                **error_detail,
                "failed_item_count": len(failed_items),
            },
        )
        await db.commit()
        await db.refresh(run)
        await self._publish_run_update(run, event)

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
        await db.flush()
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
        active_count = counts.get("pending", 0) + counts.get("queued", 0) + counts.get("running", 0)
        if run.cancel_requested:
            run.status = "canceled"
            run.finished_at = run.finished_at or datetime.now()
        elif active_count == 0:
            run.finished_at = run.finished_at or datetime.now()
            run.status = "failed" if run.succeeded_count == 0 and run.failed_count > 0 else "succeeded"
        elif run.status == "queued" and counts.get("queued", 0) + counts.get("running", 0) > 0:
            run.status = "running"
            run.started_at = run.started_at or datetime.now()

    async def _reconcile_terminal_run_counts(self, db: AsyncSession, run: AiPipelineBatchRun) -> None:
        if run.status not in {"succeeded", "failed", "canceled"}:
            return
        completed_count = (
            run.succeeded_count
            + run.failed_count
            + run.skipped_count
            + run.canceled_count
        )
        if completed_count == run.total_count:
            return
        await self._refresh_run_counts(db, run)

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
    ) -> AiPipelineBatchRunEvent:
        event = AiPipelineBatchRunEvent(
            batch_run_id=run_id,
            event_type=event_type,
            event_payload=_dump_json(payload),
        )
        db.add(event)
        await db.flush()
        return event

    async def _publish_run_update(
        self,
        run: AiPipelineBatchRun,
        event: AiPipelineBatchRunEvent,
    ) -> None:
        from .batch_stream import BatchRunStreamEvent, get_batch_run_stream_hub

        await get_batch_run_stream_hub().publish(
            BatchRunStreamEvent(
                event="batch_run_updated",
                run_id=run.run_id,
                data={
                    "run": self._to_run_response(run).model_dump(mode="json"),
                    "event": self._to_event_response(event).model_dump(mode="json"),
                },
            )
        )

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
            script_params=BatchAnnotationService._mask_script_params(_load_json(run.script_params_json, {})),
            error_message=run.error_message,
            started_at=run.started_at,
            finished_at=run.finished_at,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @staticmethod
    def _to_event_response(event: AiPipelineBatchRunEvent) -> AiPipelineBatchRunEventResponse:
        return AiPipelineBatchRunEventResponse(
            id=event.id,
            event_type=event.event_type,
            event_payload=_load_json(event.event_payload, event.event_payload),
            created_at=event.created_at,
        )

    @staticmethod
    def _to_item_response(item: AiPipelineBatchRunItem) -> AiPipelineBatchRunItemResponse:
        result = _load_json(item.result_json, None)
        error_detail = result.get("error_detail") if isinstance(result, dict) else None
        if not isinstance(error_detail, dict):
            error_detail = BatchAnnotationService._infer_error_detail(item.error_message)
        return AiPipelineBatchRunItemResponse(
            id=item.id,
            sample_item_id=item.sample_item_id,
            item_key=item.item_key,
            status=item.status,
            attempt_count=item.attempt_count,
            annotation_record_id=item.annotation_record_id,
            error_message=item.error_message,
            error_detail=error_detail,
            result=result if isinstance(result, dict) else None,
            started_at=item.started_at,
            finished_at=item.finished_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def _infer_error_detail(error_message: str | None) -> dict[str, Any] | None:
        if not error_message:
            return None
        if error_message.startswith("vision model annotation failed:"):
            detail: dict[str, Any] = {
                "source": "vision_model_api",
                "stage": "chat_completions",
                "message": error_message.removeprefix("vision model annotation failed:").strip(),
            }
            match = re.search(r"HTTP Error (\d{3})", error_message)
            if match:
                detail["http_status"] = int(match.group(1))
            return detail
        if error_message.startswith("sandbox error:"):
            return {"source": "sandbox", "stage": "execute_chunk", "message": error_message}
        if error_message.startswith("failed to save annotation result:"):
            return {"source": "automl_server", "stage": "save_annotation_record", "message": error_message}
        return None


_batch_annotation_service: BatchAnnotationService | None = None


def get_batch_annotation_service() -> BatchAnnotationService:
    global _batch_annotation_service
    if _batch_annotation_service is None:
        _batch_annotation_service = BatchAnnotationService()
    return _batch_annotation_service
