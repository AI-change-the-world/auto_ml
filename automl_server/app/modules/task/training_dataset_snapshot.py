"""Build the exploratory training runtime's S3 dataset source contract.

This module deliberately has no HTTP, MQ, or storage-write behavior. It keeps
the database-to-S3 mapping owned by the control plane while letting the future
training worker consume a framework-neutral, versioned manifest.
"""
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Iterable

from app.common.constants import TaskType
from app.common.exceptions import BadRequestException


DATASET_SOURCE_PROTOCOL_VERSION = "training-dataset-source-manifest/v1"

_TASK_METADATA: dict[int, tuple[str, str]] = {
    # BBox versus OBB is a package parameter, not an immutable source-data type.
    TaskType.DETECTION: ("detection", "detection"),
    TaskType.CLASSIFICATION: ("classification", "classification"),
    TaskType.SEGMENTATION: ("segmentation", "segmentation"),
}


class TrainingDatasetSnapshotBuilder:
    """Converts the existing resolved trainer-source payload into an S3 manifest."""

    def build(self, *, task_type: int, sources: Iterable[dict[str, Any]]) -> dict[str, Any]:
        task_kind, annotation_kind = self._task_metadata(task_type)
        source_list = list(sources)
        if not source_list:
            raise BadRequestException("at least one training source is required")

        class_names = self._shared_classes(source_list)
        items: list[dict[str, Any]] = []
        item_ids: set[str] = set()
        source_ids: set[tuple[int, int]] = set()
        source_orders: set[int] = set()
        for source in source_list:
            source_order = self._required_nonnegative_int(source, "source_order")
            dataset_id = self._required_int(source, "dataset_id")
            annotation_id = self._required_int(source, "annotation_id")
            source_id = (dataset_id, annotation_id)
            if source_id in source_ids:
                raise BadRequestException(
                    "training source snapshot must not repeat the same dataset and annotation"
                )
            if source_order in source_orders:
                raise BadRequestException("training source snapshot has duplicate source_order")
            source_ids.add(source_id)
            source_orders.add(source_order)
            samples = source.get("samples")
            if not isinstance(samples, list):
                raise BadRequestException("training source samples must be a list")
            for sample in samples:
                item = self._build_item(
                    sample=sample,
                    source_order=source_order,
                    dataset_id=dataset_id,
                    annotation_id=annotation_id,
                )
                if item["item_id"] in item_ids:
                    raise BadRequestException(
                        f"training source snapshot has duplicate item_id `{item['item_id']}`"
                    )
                item_ids.add(item["item_id"])
                items.append(item)

        if not items:
            raise BadRequestException("training source snapshot has no asset-backed annotated samples")
        return {
            "protocol_version": DATASET_SOURCE_PROTOCOL_VERSION,
            "task_kind": task_kind,
            "data_modalities": ["image"],
            "annotation_kinds": [annotation_kind],
            "class_names": class_names,
            "items": items,
        }

    @staticmethod
    def _task_metadata(task_type: int) -> tuple[str, str]:
        metadata = _TASK_METADATA.get(task_type)
        if metadata is None:
            raise BadRequestException(f"unsupported task_type for training dataset snapshot: {task_type}")
        return metadata

    def _shared_classes(self, sources: list[dict[str, Any]]) -> list[str]:
        first = self._normalise_classes(sources[0].get("classes"))
        if not first:
            raise BadRequestException("training source classes is empty")
        for source in sources[1:]:
            if self._normalise_classes(source.get("classes")) != first:
                raise BadRequestException("all training sources must share the same normalized classes")
        return first

    def _build_item(
        self,
        *,
        sample: Any,
        source_order: int,
        dataset_id: int,
        annotation_id: int,
    ) -> dict[str, Any]:
        if not isinstance(sample, dict):
            raise BadRequestException("training source sample must be an object")
        sample_item_id = self._required_int(sample, "sample_item_id")
        asset = sample.get("asset")
        annotation = sample.get("annotation")
        if not isinstance(asset, dict) or not isinstance(annotation, dict):
            raise BadRequestException(f"training source sample {sample_item_id} is missing asset or annotation")
        media_key = self._object_key(asset.get("save_path"), "asset", sample_item_id)
        annotation_key = self._annotation_key(annotation.get("storage_path"), sample_item_id)
        item_key = str(sample.get("item_key") or sample_item_id).strip()
        if not item_key:
            raise BadRequestException(f"training source sample {sample_item_id} item_key is empty")
        metadata = {
            "source_order": source_order,
            "dataset_id": dataset_id,
            "annotation_id": annotation_id,
            "sample_item_id": sample_item_id,
            "item_key": item_key,
            "asset_id": self._optional_int(asset.get("id")),
            "annotation_record_id": self._optional_int(annotation.get("id")),
            "file_name": str(asset.get("file_name") or "").strip() or None,
            "mime_type": str(asset.get("mime_type") or "").strip() or None,
            "declared_size_bytes": self._optional_int(asset.get("size_bytes")),
        }
        return {
            "item_id": f"s{source_order}-d{dataset_id}-a{annotation_id}-i{sample_item_id}",
            "split": "unspecified",
            "media": {"bucket": "datasets", "object_key": media_key},
            "annotation": {"bucket": "annotations", "object_key": annotation_key},
            "metadata": {key: value for key, value in metadata.items() if value is not None},
        }

    @staticmethod
    def _normalise_classes(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        normalised = [str(item).strip() for item in value]
        if not normalised or any(not item for item in normalised) or len(normalised) != len(set(normalised)):
            return []
        return normalised

    @staticmethod
    def _required_int(value: dict[str, Any], field: str) -> int:
        number = TrainingDatasetSnapshotBuilder._optional_int(value.get(field))
        if number is None or number <= 0:
            raise BadRequestException(f"training source {field} must be a positive integer")
        return number

    @staticmethod
    def _required_nonnegative_int(value: dict[str, Any], field: str) -> int:
        number = TrainingDatasetSnapshotBuilder._optional_int(value.get(field))
        if number is None or number < 0:
            raise BadRequestException(f"training source {field} must be a non-negative integer")
        return number

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _object_key(value: Any, label: str, sample_item_id: int) -> str:
        key = str(value or "").strip().replace("\\", "/")
        path = PurePosixPath(key)
        if not key or key == "." or path.is_absolute() or ".." in path.parts:
            raise BadRequestException(f"training source sample {sample_item_id} has invalid {label} object key")
        return key

    def _annotation_key(self, value: Any, sample_item_id: int) -> str:
        key = self._object_key(value, "annotation", sample_item_id)
        if not key.startswith("annotations/"):
            raise BadRequestException(
                f"training source sample {sample_item_id} annotation must use a persisted annotations object"
            )
        return key
