"""Immutable package and base-model registration backed by existing S3 buckets."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZipFile

from admission import ContractAdmissionError, validate_package_manifest
from contracts import (
    DatasetSourceItem,
    ModelArtifactReference,
    ModelPackageRegistration,
    S3ObjectReference,
    StorageBucket,
    TrainingDatasetSourceManifest,
    TrainingPackageRegistration,
)
from package_validation import (
    ArchiveValidationReport,
    validate_model_package_archive,
    validate_package_archive,
)
from storage import ObjectStorage, content_reference, registration_json


class PackageRegistryError(RuntimeError):
    """An immutable package or model release could not be registered."""


@dataclass(frozen=True)
class PackageRegistrationResult:
    registration: TrainingPackageRegistration
    created: bool


@dataclass(frozen=True)
class ModelPackageRegistrationResult:
    registration: ModelPackageRegistration
    created: bool


@dataclass(frozen=True)
class DatasetSnapshotRegistration:
    source_manifest: TrainingDatasetSourceManifest
    object: S3ObjectReference
    created: bool


class TrainingPackageRegistry:
    """Stores releases by content digest; key/version never silently overwrite."""

    def __init__(self, storage: ObjectStorage) -> None:
        self.storage = storage

    async def register_package(
        self,
        *,
        archive_name: str,
        archive_bytes: bytes,
    ) -> PackageRegistrationResult:
        report = validate_package_archive(archive_bytes)
        try:
            validate_package_manifest(report.manifest)
        except ContractAdmissionError as exc:
            raise PackageRegistryError(str(exc)) from exc
        file_name = _file_name(archive_name, fallback="training-package.zip")
        archive = content_reference(
            StorageBucket.DEFAULT,
            _package_archive_key(report),
            archive_bytes,
        )
        registration = TrainingPackageRegistration(
            manifest=report.manifest,
            archive=archive,
            package_file_name=file_name,
        )
        marker_location = S3ObjectReference(
            bucket=StorageBucket.DEFAULT,
            object_key=_package_registration_key(report),
        )
        if await self.storage.exists(marker_location):
            existing = await self._read_package_registration(marker_location)
            if existing.archive.sha256 == archive.sha256:
                return PackageRegistrationResult(registration=existing, created=False)
            raise PackageRegistryError(
                f"package `{report.manifest.key}` version `{report.manifest.version}` already exists with a different archive digest"
            )

        if not await self.storage.exists(archive):
            await self.storage.write(archive, archive_bytes)
        marker_payload = registration_json(archive, {"registration": registration.model_dump(mode="json")})
        marker = content_reference(StorageBucket.DEFAULT, marker_location.object_key, marker_payload)
        await self.storage.write(marker, marker_payload)
        return PackageRegistrationResult(registration=registration, created=True)

    async def register_model_package(
        self,
        *,
        archive_name: str,
        archive_bytes: bytes,
    ) -> ModelPackageRegistrationResult:
        """Import a manifest-declared ZIP into immutable models-bucket objects.

        The ZIP remains as an audit source. Its selected weight and optional
        resume checkpoint are also stored as individual immutable objects so a
        worker never needs to trust arbitrary ZIP-member selection at runtime.
        """
        report = validate_model_package_archive(archive_bytes)
        marker_location = S3ObjectReference(
            bucket=StorageBucket.MODELS,
            object_key=_model_package_registration_key(report.sha256),
        )
        if await self.storage.exists(marker_location):
            return ModelPackageRegistrationResult(
                registration=await self._read_model_package_registration(marker_location),
                created=False,
            )

        archive = content_reference(
            StorageBucket.MODELS,
            _model_package_archive_key(report.sha256),
            archive_bytes,
        )
        with ZipFile(BytesIO(archive_bytes)) as bundle:
            initialize_bytes = bundle.read(report.manifest.artifact_path)
            resume_bytes = (
                bundle.read(report.manifest.resume_checkpoint_path)
                if report.manifest.resume_checkpoint_path is not None
                else None
            )
        if not initialize_bytes:
            raise PackageRegistryError("model package artifact_path must not be empty")
        if resume_bytes is not None and not resume_bytes:
            raise PackageRegistryError("model package resume_checkpoint_path must not be empty")

        initialize_reference = content_reference(
            StorageBucket.MODELS,
            _model_package_artifact_key(report.sha256, "initialize", report.manifest.format),
            initialize_bytes,
        )
        initialize_artifact = ModelArtifactReference(
            source="uploaded_model_package",
            object=initialize_reference,
            format=report.manifest.format,
            task_kind=report.manifest.task_kind,
            class_names=report.manifest.class_names,
            display_name=report.manifest.name,
            framework=report.manifest.framework,
            metadata=report.manifest.metadata,
        )
        resume_artifact = None
        if resume_bytes is not None:
            resume_reference = content_reference(
                StorageBucket.MODELS,
                _model_package_artifact_key(report.sha256, "resume-checkpoint", report.manifest.format),
                resume_bytes,
            )
            resume_artifact = ModelArtifactReference(
                source="uploaded_model_package",
                object=resume_reference,
                format=report.manifest.format,
                task_kind=report.manifest.task_kind,
                class_names=report.manifest.class_names,
                display_name=f"{report.manifest.name} (resume checkpoint)",
                framework=report.manifest.framework,
                resume_supported=True,
                metadata=report.manifest.metadata,
            )
        registration = ModelPackageRegistration(
            manifest=report.manifest,
            archive=archive,
            package_file_name=_file_name(archive_name, fallback="training-model-package.zip"),
            initialize_artifact=initialize_artifact,
            resume_artifact=resume_artifact,
        )
        for reference, content in (
            (archive, archive_bytes),
            (initialize_reference, initialize_bytes),
            *(((resume_artifact.object, resume_bytes),) if resume_artifact else ()),
        ):
            if not await self.storage.exists(reference):
                await self.storage.write(reference, content)
        marker_payload = registration_json(archive, {"registration": registration.model_dump(mode="json")})
        marker = content_reference(StorageBucket.MODELS, marker_location.object_key, marker_payload)
        await self.storage.write(marker, marker_payload)
        return ModelPackageRegistrationResult(registration=registration, created=True)

    async def register_dataset_snapshot(
        self,
        source_manifest: TrainingDatasetSourceManifest,
    ) -> DatasetSnapshotRegistration:
        """Pin current-platform S3 paths, then persist their resolved source list."""
        pinned_items = []
        for item in source_manifest.items:
            pinned_items.append(
                DatasetSourceItem(
                    item_id=item.item_id,
                    split=item.split,
                    media=await self._pin_object(item.media),
                    annotation=(await self._pin_object(item.annotation)) if item.annotation else None,
                    metadata=item.metadata,
                )
            )
        snapshot_manifest = source_manifest.model_copy(update={"items": pinned_items})
        payload = json.dumps(
            snapshot_manifest.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        reference = content_reference(
            StorageBucket.DEFAULT,
            f"training-code-runtime/dataset-snapshots/{digest}.json",
            payload,
        )
        created = not await self.storage.exists(reference)
        if created:
            await self.storage.write(reference, payload)
        return DatasetSnapshotRegistration(
            source_manifest=snapshot_manifest,
            object=reference,
            created=created,
        )

    async def _pin_object(self, reference: S3ObjectReference) -> S3ObjectReference:
        content = await self.storage.read(reference)
        return content_reference(reference.bucket, reference.object_key, content)

    async def _read_package_registration(self, reference) -> TrainingPackageRegistration:
        try:
            payload = json.loads((await self.storage.read(reference)).decode("utf-8"))
            return TrainingPackageRegistration.model_validate(payload["registration"])
        except Exception as exc:
            raise PackageRegistryError(
                f"stored package registration is unreadable: {reference.object_key}"
            ) from exc

    async def _read_model_package_registration(self, reference) -> ModelPackageRegistration:
        try:
            payload = json.loads((await self.storage.read(reference)).decode("utf-8"))
            return ModelPackageRegistration.model_validate(payload["registration"])
        except Exception as exc:
            raise PackageRegistryError(
                f"stored model package registration is unreadable: {reference.object_key}"
            ) from exc


def _package_archive_key(report: ArchiveValidationReport) -> str:
    return (
        f"training-code-runtime/packages/{report.manifest.key}/"
        f"{report.manifest.version}/{report.sha256}.zip"
    )


def _package_registration_key(report: ArchiveValidationReport) -> str:
    return (
        f"training-code-runtime/packages/{report.manifest.key}/"
        f"{report.manifest.version}/registration.json"
    )


def _model_package_archive_key(digest: str) -> str:
    return f"training-code-runtime/model-packages/{digest}/source.zip"


def _model_package_artifact_key(digest: str, role: str, artifact_format: str) -> str:
    return f"training-code-runtime/model-packages/{digest}/{role}.{artifact_format}"


def _model_package_registration_key(digest: str) -> str:
    return f"training-code-runtime/model-packages/{digest}/registration.json"


def _file_name(value: str, *, fallback: str) -> str:
    normalized = PurePosixPath((value or "").replace("\\", "/")).name.strip()
    return normalized[:255] if normalized else fallback
