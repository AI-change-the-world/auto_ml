"""Control-plane catalog for custom training runtime ZIP releases."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BadRequestException
from app.config.settings import get_settings
from app.db.models import TrainingRuntimeCodePackage, TrainingRuntimeModelPackage

from .registration import TrainingRuntimeRegistrar
from .schemas import (
    TrainingRuntimeCodePackageImportResponse,
    TrainingRuntimeCodePackageResponse,
    TrainingRuntimeModelPackageImportResponse,
    TrainingRuntimeModelPackageResponse,
)


class TrainingRuntimeCatalogService:
    """Registers and exposes runtime-only artifacts; it never creates a task."""

    async def list_code_packages(
        self,
        db: AsyncSession,
        *,
        include_disabled: bool = False,
    ) -> list[TrainingRuntimeCodePackageResponse]:
        conditions = [TrainingRuntimeCodePackage.is_deleted == False]
        if not include_disabled:
            conditions.append(TrainingRuntimeCodePackage.enabled == True)
        rows = list(
            (
                await db.execute(
                    select(TrainingRuntimeCodePackage)
                    .where(*conditions)
                    .order_by(
                        TrainingRuntimeCodePackage.package_key.asc(),
                        TrainingRuntimeCodePackage.created_at.desc(),
                        TrainingRuntimeCodePackage.id.desc(),
                    )
                )
            ).scalars().all()
        )
        return [self._serialize_code_package(row) for row in rows]

    async def import_code_package(
        self,
        db: AsyncSession,
        *,
        archive_name: str,
        archive_bytes: bytes,
    ) -> TrainingRuntimeCodePackageImportResponse:
        registration_result = await self._registrar().register_code_package(
            archive_name=archive_name,
            archive_bytes=archive_bytes,
        )
        registration = registration_result.registration
        manifest = registration.manifest
        existing = await db.scalar(
            select(TrainingRuntimeCodePackage).where(
                TrainingRuntimeCodePackage.package_key == manifest.key,
                TrainingRuntimeCodePackage.version == manifest.version,
            )
        )
        if existing is not None:
            if existing.package_sha256 != registration.archive.sha256:
                raise BadRequestException(
                    f"training package `{manifest.key}` version `{manifest.version}` "
                    "already exists with a different archive digest"
                )
            return TrainingRuntimeCodePackageImportResponse(
                package=self._serialize_code_package(existing),
                registration_created=registration_result.created,
                catalog_created=False,
            )

        runtime_id = str(manifest.runtime.get("id") or "").strip()
        if not runtime_id:
            raise BadRequestException("training runtime package registration is missing runtime.id")
        package = TrainingRuntimeCodePackage(
            package_key=manifest.key,
            version=manifest.version,
            name=manifest.name,
            description=manifest.description,
            runtime_id=runtime_id,
            entrypoint=manifest.entrypoint,
            package_object_key=registration.archive.object_key,
            package_sha256=registration.archive.sha256,
            package_size_bytes=registration.archive.size_bytes,
            package_file_name=registration.package_file_name,
            supported_tasks_json=self._dump(manifest.supported_tasks),
            parameters_schema_json=self._dump(manifest.parameters_schema),
            model_input_contract_json=(
                self._dump(manifest.model_input_contract)
                if manifest.model_input_contract is not None
                else None
            ),
            output_contract_json=self._dump(manifest.output_contract),
        )
        db.add(package)
        await db.commit()
        await db.refresh(package)
        return TrainingRuntimeCodePackageImportResponse(
            package=self._serialize_code_package(package),
            registration_created=registration_result.created,
            catalog_created=True,
        )

    async def list_model_packages(
        self,
        db: AsyncSession,
        *,
        include_disabled: bool = False,
    ) -> list[TrainingRuntimeModelPackageResponse]:
        conditions = [TrainingRuntimeModelPackage.is_deleted == False]
        if not include_disabled:
            conditions.append(TrainingRuntimeModelPackage.enabled == True)
        rows = list(
            (
                await db.execute(
                    select(TrainingRuntimeModelPackage)
                    .where(*conditions)
                    .order_by(
                        TrainingRuntimeModelPackage.created_at.desc(),
                        TrainingRuntimeModelPackage.id.desc(),
                    )
                )
            ).scalars().all()
        )
        return [self._serialize_model_package(row) for row in rows]

    async def import_model_package(
        self,
        db: AsyncSession,
        *,
        archive_name: str,
        archive_bytes: bytes,
    ) -> TrainingRuntimeModelPackageImportResponse:
        registration_result = await self._registrar().register_model_package(
            archive_name=archive_name,
            archive_bytes=archive_bytes,
        )
        registration = registration_result.registration
        existing = await db.scalar(
            select(TrainingRuntimeModelPackage).where(
                TrainingRuntimeModelPackage.package_sha256 == registration.archive.sha256,
            )
        )
        if existing is not None:
            return TrainingRuntimeModelPackageImportResponse(
                package=self._serialize_model_package(existing),
                registration_created=registration_result.created,
                catalog_created=False,
            )

        manifest = registration.manifest
        initialize = registration.initialize_artifact
        resume = registration.resume_artifact
        package = TrainingRuntimeModelPackage(
            name=manifest.name,
            package_object_key=registration.archive.object_key,
            package_sha256=registration.archive.sha256,
            package_size_bytes=registration.archive.size_bytes,
            package_file_name=registration.package_file_name,
            task_kind=manifest.task_kind,
            class_names_json=self._dump(manifest.class_names),
            framework_id=manifest.framework.id,
            framework_version=manifest.framework.version,
            artifact_format=manifest.format,
            initialize_object_key=initialize.object.object_key,
            initialize_sha256=initialize.object.sha256,
            initialize_size_bytes=initialize.object.size_bytes,
            resume_object_key=resume.object.object_key if resume is not None else None,
            resume_sha256=resume.object.sha256 if resume is not None else None,
            resume_size_bytes=resume.object.size_bytes if resume is not None else None,
            metadata_json=self._dump(manifest.metadata),
        )
        db.add(package)
        await db.commit()
        await db.refresh(package)
        return TrainingRuntimeModelPackageImportResponse(
            package=self._serialize_model_package(package),
            registration_created=registration_result.created,
            catalog_created=True,
        )

    @staticmethod
    def _registrar() -> TrainingRuntimeRegistrar:
        settings = get_settings().training_code_runtime
        if not settings.enabled or not settings.base_url.strip():
            raise BadRequestException("model training runtime package registration is disabled")
        return TrainingRuntimeRegistrar(
            base_url=settings.base_url,
            timeout=settings.timeout,
            token=settings.token,
        )

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _load(value: str | None, fallback: Any) -> Any:
        if not value:
            return fallback
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return fallback

    def _serialize_code_package(
        self,
        row: TrainingRuntimeCodePackage,
    ) -> TrainingRuntimeCodePackageResponse:
        return TrainingRuntimeCodePackageResponse(
            id=row.id,
            package_key=row.package_key,
            version=row.version,
            name=row.name,
            description=row.description,
            runtime_id=row.runtime_id,
            entrypoint=row.entrypoint,
            package_sha256=row.package_sha256,
            package_size_bytes=row.package_size_bytes,
            package_file_name=row.package_file_name,
            supported_tasks=self._load(row.supported_tasks_json, []),
            parameters_schema=self._load(row.parameters_schema_json, {}),
            model_input_contract=self._load(row.model_input_contract_json, None),
            output_contract=self._load(row.output_contract_json, {}),
            enabled=row.enabled,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _serialize_model_package(
        self,
        row: TrainingRuntimeModelPackage,
    ) -> TrainingRuntimeModelPackageResponse:
        return TrainingRuntimeModelPackageResponse(
            id=row.id,
            name=row.name,
            package_sha256=row.package_sha256,
            package_size_bytes=row.package_size_bytes,
            package_file_name=row.package_file_name,
            task_kind=row.task_kind,
            class_names=self._load(row.class_names_json, []),
            framework_id=row.framework_id,
            framework_version=row.framework_version,
            artifact_format=row.artifact_format,
            initialize_sha256=row.initialize_sha256,
            initialize_size_bytes=row.initialize_size_bytes,
            has_resume_checkpoint=bool(row.resume_object_key),
            metadata=self._load(row.metadata_json, {}),
            enabled=row.enabled,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


_training_runtime_catalog_service: TrainingRuntimeCatalogService | None = None


def get_training_runtime_catalog_service() -> TrainingRuntimeCatalogService:
    global _training_runtime_catalog_service
    if _training_runtime_catalog_service is None:
        _training_runtime_catalog_service = TrainingRuntimeCatalogService()
    return _training_runtime_catalog_service
