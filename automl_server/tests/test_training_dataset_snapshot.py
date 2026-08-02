import unittest
import asyncio
import importlib.util
import sys
import types
from unittest.mock import AsyncMock
from pathlib import Path

from app.common.exceptions import BadRequestException
from app.common.constants import TaskType


MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "modules" / "task" / "training_dataset_snapshot.py"
SPEC = importlib.util.spec_from_file_location("training_dataset_snapshot_test_module", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load training dataset snapshot builder")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
TrainingDatasetSnapshotBuilder = MODULE.TrainingDatasetSnapshotBuilder

RUNTIME_CONTRACTS_PATH = Path(__file__).resolve().parents[2] / "model_training_runtime" / "contracts.py"
RUNTIME_SPEC = importlib.util.spec_from_file_location("model_training_runtime_contracts_test_module", RUNTIME_CONTRACTS_PATH)
if RUNTIME_SPEC is None or RUNTIME_SPEC.loader is None:
    raise RuntimeError("unable to load training runtime contracts")
RUNTIME_MODULE = importlib.util.module_from_spec(RUNTIME_SPEC)
# Pydantic resolves postponed annotations through the module registry.
sys.modules[RUNTIME_SPEC.name] = RUNTIME_MODULE
RUNTIME_SPEC.loader.exec_module(RUNTIME_MODULE)
TrainingDatasetSourceManifest = RUNTIME_MODULE.TrainingDatasetSourceManifest

SCHEMAS_PATH = Path(__file__).resolve().parents[1] / "app" / "modules" / "task" / "schemas.py"
SCHEMAS_SPEC = importlib.util.spec_from_file_location("training_dataset_snapshot_schemas_test_module", SCHEMAS_PATH)
if SCHEMAS_SPEC is None or SCHEMAS_SPEC.loader is None:
    raise RuntimeError("unable to load training dataset snapshot schemas")
SCHEMAS_MODULE = importlib.util.module_from_spec(SCHEMAS_SPEC)
sys.modules[SCHEMAS_SPEC.name] = SCHEMAS_MODULE
sys.modules["app.modules.task.schemas"] = SCHEMAS_MODULE
SCHEMAS_SPEC.loader.exec_module(SCHEMAS_MODULE)
TrainingDatasetSnapshotPreviewRequest = SCHEMAS_MODULE.TrainingDatasetSnapshotPreviewRequest
TrainingDatasetSnapshotPreviewResponse = SCHEMAS_MODULE.TrainingDatasetSnapshotPreviewResponse
TrainingDatasetSnapshotRegistrationResponse = SCHEMAS_MODULE.TrainingDatasetSnapshotRegistrationResponse

REGISTRAR_PATH = Path(__file__).resolve().parents[1] / "app" / "modules" / "task" / "training_dataset_registration.py"
# Avoid importing app.modules, whose package initializer eagerly loads all APIs.
task_package = types.ModuleType("app.modules.task")
task_package.__path__ = [str(REGISTRAR_PATH.parent)]
sys.modules["app.modules.task"] = task_package
http_client_module = types.ModuleType("app.utils.http_client")


class _UnusedHttpClient:
    def __init__(self, *args, **kwargs) -> None:
        pass


http_client_module.HttpClient = _UnusedHttpClient
sys.modules["app.utils.http_client"] = http_client_module
REGISTRAR_SPEC = importlib.util.spec_from_file_location(
    "app.modules.task.training_dataset_registration",
    REGISTRAR_PATH,
)
if REGISTRAR_SPEC is None or REGISTRAR_SPEC.loader is None:
    raise RuntimeError("unable to load training dataset snapshot registrar")
REGISTRAR_MODULE = importlib.util.module_from_spec(REGISTRAR_SPEC)
sys.modules[REGISTRAR_SPEC.name] = REGISTRAR_MODULE
REGISTRAR_SPEC.loader.exec_module(REGISTRAR_MODULE)
validate_registered_snapshot = REGISTRAR_MODULE._validate_registered_snapshot
TrainingDatasetSnapshotRegistrar = REGISTRAR_MODULE.TrainingDatasetSnapshotRegistrar


def source(*, source_order: int = 0, sample_id: int = 101, annotation_path: str = "annotations/a/records/101.txt") -> dict:
    return {
        "dataset_id": 11,
        "annotation_id": 21,
        "source_order": source_order,
        "classes": ["cat", "dog"],
        "samples": [
            {
                "sample_item_id": sample_id,
                "item_key": "cat-image",
                "asset": {
                    "id": 31,
                    "file_name": "cat.jpg",
                    "save_path": "datasets/11/cat.jpg",
                    "mime_type": "image/jpeg",
                    "size_bytes": 256,
                },
                "annotation": {
                    "id": 41,
                    "storage_path": annotation_path,
                },
            }
        ],
    }


class TrainingDatasetSnapshotBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = TrainingDatasetSnapshotBuilder()

    def test_builds_framework_neutral_s3_manifest_from_existing_sources(self) -> None:
        manifest = self.builder.build(task_type=TaskType.CLASSIFICATION, sources=[source()])

        self.assertEqual(manifest["protocol_version"], "training-dataset-source-manifest/v1")
        self.assertEqual(manifest["task_kind"], "classification")
        self.assertEqual(manifest["annotation_kinds"], ["classification"])
        self.assertEqual(manifest["class_names"], ["cat", "dog"])
        self.assertEqual(manifest["items"][0]["media"], {
            "bucket": "datasets",
            "object_key": "datasets/11/cat.jpg",
        })
        self.assertEqual(manifest["items"][0]["annotation"], {
            "bucket": "annotations",
            "object_key": "annotations/a/records/101.txt",
        })
        self.assertEqual(manifest["items"][0]["metadata"]["sample_item_id"], 101)
        # The control-plane preview must be acceptable to the runtime registry.
        validated = TrainingDatasetSourceManifest.model_validate(manifest)
        self.assertEqual(validated.items[0].media.bucket.value, "datasets")
        response = TrainingDatasetSnapshotPreviewResponse(
            manifest=manifest,
            source_count=1,
            sample_count=1,
        )
        self.assertEqual(response.manifest.task_kind, "classification")
        registered_manifest = response.manifest.model_dump(mode="json")
        registered_manifest["items"][0]["media"].update({"sha256": "a" * 64, "size_bytes": 256})
        registered_manifest["items"][0]["annotation"].update({"sha256": "b" * 64, "size_bytes": 32})
        registered = TrainingDatasetSnapshotRegistrationResponse(
            created=True,
            manifest=registered_manifest,
            object={
                "bucket": "default",
                "object_key": f"training-code-runtime/dataset-snapshots/{'c' * 64}.json",
                "sha256": "c" * 64,
                "size_bytes": 512,
            },
            source_count=1,
            sample_count=1,
        )
        validate_registered_snapshot(response.manifest, registered)

        registered.manifest.items[0].media.object_key = "datasets/other.jpg"
        with self.assertRaises(ValueError):
            validate_registered_snapshot(response.manifest, registered)

    def test_rejects_missing_persisted_annotation_and_unsafe_object_path(self) -> None:
        with self.assertRaises(BadRequestException):
            self.builder.build(
                task_type=TaskType.DETECTION,
                sources=[source(annotation_path="")],
            )

        unsafe = source()
        unsafe["samples"][0]["asset"]["save_path"] = "../assets/cat.jpg"
        with self.assertRaises(BadRequestException):
            self.builder.build(task_type=TaskType.DETECTION, sources=[unsafe])

    def test_requires_one_consistent_class_order_across_sources(self) -> None:
        first = source(source_order=0, sample_id=101)
        second = source(source_order=1, sample_id=102)
        second["dataset_id"] = 12
        second["annotation_id"] = 22
        second["classes"] = ["dog", "cat"]
        with self.assertRaises(BadRequestException):
            self.builder.build(task_type=TaskType.SEGMENTATION, sources=[first, second])

    def test_rejects_duplicate_source_selection_and_source_order(self) -> None:
        first = source(source_order=0, sample_id=101)
        repeated = source(source_order=1, sample_id=102)
        with self.assertRaises(BadRequestException):
            self.builder.build(task_type=TaskType.CLASSIFICATION, sources=[first, repeated])

        second = source(source_order=0, sample_id=102)
        second["dataset_id"] = 12
        second["annotation_id"] = 22
        with self.assertRaises(BadRequestException):
            self.builder.build(task_type=TaskType.CLASSIFICATION, sources=[first, second])

    def test_preview_request_has_one_unambiguous_source_selector(self) -> None:
        direct = TrainingDatasetSnapshotPreviewRequest(dataset_id=11, annotation_id=21)
        self.assertEqual(direct.task_type, 0)

        selected = TrainingDatasetSnapshotPreviewRequest(
            task_type=1,
            sources=[{"dataset_id": 11, "annotation_id": 21}],
        )
        self.assertEqual(selected.sources[0].dataset_id, 11)

        with self.assertRaises(ValueError):
            TrainingDatasetSnapshotPreviewRequest(dataset_id=11)
        with self.assertRaises(ValueError):
            TrainingDatasetSnapshotPreviewRequest(
                dataset_id=11,
                annotation_id=21,
                sources=[{"dataset_id": 12, "annotation_id": 22}],
            )
        with self.assertRaises(ValueError):
            TrainingDatasetSnapshotPreviewRequest(
                sources=[
                    {"dataset_id": 11, "annotation_id": 21},
                    {"dataset_id": 11, "annotation_id": 21},
                ]
            )
        with self.assertRaises(ValueError):
            TrainingDatasetSnapshotPreviewRequest(dataset_id=11, annotation_id=21, unexpected=True)

    def test_registrar_sends_bearer_token_and_accepts_only_pinned_response(self) -> None:
        manifest = TrainingDatasetSnapshotPreviewResponse(
            manifest=self.builder.build(task_type=TaskType.CLASSIFICATION, sources=[source()]),
            source_count=1,
            sample_count=1,
        ).manifest
        pinned_manifest = manifest.model_dump(mode="json")
        pinned_manifest["items"][0]["media"].update({"sha256": "a" * 64, "size_bytes": 256})
        pinned_manifest["items"][0]["annotation"].update({"sha256": "b" * 64, "size_bytes": 32})
        payload = {
            "created": False,
            "registration": {
                "source_manifest": pinned_manifest,
                "object": {
                    "bucket": "default",
                    "object_key": f"training-code-runtime/dataset-snapshots/{'c' * 64}.json",
                    "sha256": "c" * 64,
                    "size_bytes": 512,
                },
            },
        }
        response = types.SimpleNamespace(status_code=200, json=lambda: payload)
        registrar = TrainingDatasetSnapshotRegistrar(
            base_url="http://model-training-runtime:8012",
            timeout=30,
            token="runtime-token",
        )
        registrar._client.post = AsyncMock(return_value=response)

        registered = asyncio.run(registrar.register(manifest, source_count=1))

        self.assertFalse(registered.created)
        self.assertEqual(registered.object.sha256, "c" * 64)
        self.assertEqual(
            registrar._client.post.await_args.kwargs["headers"],
            {"Authorization": "Bearer runtime-token"},
        )


if __name__ == "__main__":
    unittest.main()
