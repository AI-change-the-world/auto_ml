"""OpenDAL-backed S3 storage adapters for future training package workflows."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol

from contracts import (
    DATASET_PROTOCOL_VERSION,
    DatasetItem,
    S3ObjectReference,
    StorageBucket,
    TrainingDatasetManifest,
    TrainingDatasetSourceManifest,
)
from runtime.logging_utils import logger


def _config_section(payload: dict, name: str) -> dict:
    value = payload.get(name)
    return value if isinstance(value, dict) else {}


def _configured_value(
    sections: tuple[dict, ...],
    config_key: str,
    env_name: str,
    fallback: str,
) -> str:
    for section in sections:
        value = section.get(config_key)
        if value is not None and value != "":
            return str(value)
    return os.getenv(env_name, fallback)


class ObjectStorageError(RuntimeError):
    """S3 storage operation or integrity verification failed."""


@dataclass(frozen=True)
class S3StorageSettings:
    endpoint: str
    access_key: str
    secret_key: str
    region: str
    default_bucket: str
    datasets_bucket: str
    models_bucket: str
    annotations_bucket: str


def load_s3_storage_settings() -> S3StorageSettings:
    """Load the same `S3_*` values used by existing OpenDAL services.

    A later Nacos listener can refresh these resolved values; callers never use
    package-provided endpoint or credential values.
    """
    config = _load_platform_config()
    storage = _config_section(config, "local-s3-config")
    training = _config_section(config, "training-code-runtime")
    training_storage = _config_section(training, "storage")
    sections = (training_storage, storage)
    return S3StorageSettings(
        endpoint=_configured_value(sections, "endpoint", "S3_ENDPOINT", "http://127.0.0.1:9000"),
        access_key=_configured_value(sections, "access_key", "S3_ACCESS_KEY", ""),
        secret_key=_configured_value(sections, "secret_key", "S3_SECRET_KEY", ""),
        region=_configured_value(sections, "region", "S3_REGION", "us-east-1"),
        default_bucket=_configured_value(sections, "bucket_name", "S3_DEFAULT_BUCKET", "auto-ml-datasets"),
        datasets_bucket=_configured_value(sections, "datasets_bucket_name", "S3_DATASETS_BUCKET", "auto-ml-datasets"),
        models_bucket=_configured_value(sections, "models_bucket_name", "S3_MODELS_BUCKET", "auto-ml-models"),
        annotations_bucket=_configured_value(sections, "annotations_bucket_name", "S3_ANNOTATIONS_BUCKET", "auto-ml-annotations"),
    )


def _load_platform_config() -> dict:
    """Read the same Nacos-provided mapping used by sandbox-backed services.

    The configuration package is optional during local contract tests. Runtime
    settings remain platform-owned; package uploads never supply S3 details.
    """
    if os.getenv("USE_NACOS", "true").lower() != "true":
        return {}
    try:
        from nacos_config_center import get_config_center

        config = get_config_center().get_config_data()
        return config if isinstance(config, dict) else {}
    except ModuleNotFoundError:
        return _load_nacos_config_directly()
    except Exception as exc:
        logger.warning("Unable to read training runtime Nacos storage settings: %s", exc)
        return {}


def _load_nacos_config_directly() -> dict:
    """Use Sandbox-compatible Nacos coordinates without duplicating S3 config."""
    try:
        import nacos
        import yaml

        client = nacos.NacosClient(
            os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848"),
            namespace=os.getenv("NACOS_NAMESPACE", "public"),
        )
        raw_config = client.get_config(
            os.getenv("NACOS_DATA_ID", "AUTO_ML_CONFIG"),
            os.getenv("NACOS_GROUP", "AUTO_ML"),
        )
        parsed = yaml.safe_load(raw_config or "") or {}
        return parsed if isinstance(parsed, dict) else {}
    except Exception as exc:
        logger.warning("Unable to read training runtime Nacos storage settings: %s", exc)
        return {}


class ObjectStorage(Protocol):
    async def read(self, reference: S3ObjectReference) -> bytes: ...

    async def write(self, reference: S3ObjectReference, content: bytes) -> None: ...

    async def exists(self, reference: S3ObjectReference) -> bool: ...


class OpenDalS3Storage:
    """Uses the repository's OpenDAL S3 pattern with one operator per bucket."""

    def __init__(self, settings: S3StorageSettings | None = None) -> None:
        self.settings = settings or load_s3_storage_settings()
        operator_kwargs = {
            "endpoint": self.settings.endpoint,
            "access_key_id": self.settings.access_key,
            "secret_access_key": self.settings.secret_key,
            "region": self.settings.region,
            "disable_ec2_metadata": "true",
        }
        try:
            import opendal
        except ModuleNotFoundError as exc:
            raise ObjectStorageError(
                "opendal is required for S3-backed training package registration; "
                "install training_code_runtime requirements"
            ) from exc
        self._operators = {
            bucket: opendal.AsyncOperator("s3", bucket=self._bucket_name(bucket), **operator_kwargs)
            for bucket in StorageBucket
        }

    async def read(self, reference: S3ObjectReference) -> bytes:
        try:
            content = bytes(await self._operator(reference.bucket).read(reference.object_key))
        except Exception as exc:
            raise ObjectStorageError(
                f"unable to read {reference.bucket.value}:{reference.object_key}: {exc}"
            ) from exc
        _verify_content(reference, content)
        logger.info(
            "Read training storage object: bucket=%s object_key=%s bytes=%s",
            reference.bucket.value,
            reference.object_key,
            len(content),
        )
        return content

    async def write(self, reference: S3ObjectReference, content: bytes) -> None:
        _verify_content(reference, content)
        try:
            await self._operator(reference.bucket).write(reference.object_key, content)
        except Exception as exc:
            raise ObjectStorageError(
                f"unable to write {reference.bucket.value}:{reference.object_key}: {exc}"
            ) from exc
        logger.info(
            "Wrote training storage object: bucket=%s object_key=%s bytes=%s",
            reference.bucket.value,
            reference.object_key,
            len(content),
        )

    async def exists(self, reference: S3ObjectReference) -> bool:
        try:
            await self._operator(reference.bucket).stat(reference.object_key)
            return True
        except Exception:
            return False

    def _operator(self, bucket: StorageBucket):
        return self._operators[bucket]

    def _bucket_name(self, bucket: StorageBucket) -> str:
        bucket_names = {
            StorageBucket.DEFAULT: self.settings.default_bucket,
            StorageBucket.DATASETS: self.settings.datasets_bucket,
            StorageBucket.MODELS: self.settings.models_bucket,
            StorageBucket.ANNOTATIONS: self.settings.annotations_bucket,
        }
        return bucket_names[bucket]


class DatasetMaterializer:
    """Converts existing S3 source manifests into runner-local dataset manifests."""

    def __init__(self, storage: ObjectStorage) -> None:
        self.storage = storage

    async def materialize(
        self,
        source_manifest: TrainingDatasetSourceManifest,
        input_dir: Path,
    ) -> TrainingDatasetManifest:
        input_dir.mkdir(parents=True, exist_ok=True)
        items: list[DatasetItem] = []
        for index, source_item in enumerate(source_manifest.items):
            _require_immutable_reference(source_item.media, "dataset media")
            item_dir = input_dir / "dataset" / f"{index:08d}_{_safe_name(source_item.item_id)}"
            media_name = _safe_name(PurePosixPath(source_item.media.object_key).name) or "media"
            media_path = item_dir / media_name
            media_path.parent.mkdir(parents=True, exist_ok=True)
            media_path.write_bytes(await self.storage.read(source_item.media))

            annotation_path: Path | None = None
            if source_item.annotation is not None:
                _require_immutable_reference(source_item.annotation, "dataset annotation")
                annotation_name = _safe_name(PurePosixPath(source_item.annotation.object_key).name) or "annotation"
                annotation_path = item_dir / annotation_name
                annotation_path.write_bytes(await self.storage.read(source_item.annotation))
            items.append(
                DatasetItem(
                    item_id=source_item.item_id,
                    split=source_item.split,
                    media_path=media_path.relative_to(input_dir).as_posix(),
                    annotation_path=(annotation_path.relative_to(input_dir).as_posix() if annotation_path else None),
                    metadata=source_item.metadata,
                )
            )

        manifest = TrainingDatasetManifest(
            protocol_version=DATASET_PROTOCOL_VERSION,
            task_kind=source_manifest.task_kind,
            data_modalities=source_manifest.data_modalities,
            annotation_kinds=source_manifest.annotation_kinds,
            class_names=source_manifest.class_names,
            items=items,
        )
        (input_dir / "dataset-manifest.json").write_text(
            manifest.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest


class ModelInputMaterializer:
    """Downloads the already-selected immutable model input below `input_dir`."""

    def __init__(self, storage: ObjectStorage) -> None:
        self.storage = storage

    async def materialize(self, reference: S3ObjectReference, input_dir: Path, *, file_name: str) -> Path:
        _require_immutable_reference(reference, "model input")
        safe_file_name = _safe_name(file_name) or "model-input"
        destination = input_dir / "model-input" / safe_file_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(await self.storage.read(reference))
        return destination


def _verify_content(reference: S3ObjectReference, content: bytes) -> None:
    if reference.size_bytes is not None and len(content) != reference.size_bytes:
        raise ObjectStorageError(
            f"object size mismatch for {reference.bucket.value}:{reference.object_key}: "
            f"expected {reference.size_bytes}, got {len(content)}"
        )
    if reference.sha256 is not None:
        digest = hashlib.sha256(content).hexdigest()
        if digest != reference.sha256:
            raise ObjectStorageError(
            f"object SHA-256 mismatch for {reference.bucket.value}:{reference.object_key}"
        )


def _require_immutable_reference(reference: S3ObjectReference, label: str) -> None:
    if reference.sha256 is None or reference.size_bytes is None:
        raise ObjectStorageError(f"{label} must include immutable SHA-256 and size_bytes")


def content_reference(bucket: StorageBucket, object_key: str, content: bytes) -> S3ObjectReference:
    """Build a fully immutable reference for content about to be written."""
    return S3ObjectReference(
        bucket=bucket,
        object_key=object_key,
        sha256=hashlib.sha256(content).hexdigest(),
        size_bytes=len(content),
    )


def registration_json(reference: S3ObjectReference, payload: dict) -> bytes:
    """Serialize immutable registration metadata deterministically for storage."""
    return json.dumps(
        {"reference": reference.model_dump(mode="json"), **payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _safe_name(value: str) -> str:
    sanitized = "".join(character if character.isalnum() or character in {"-", "_", "."} else "_" for character in value)
    return sanitized.strip("._")[:180]
