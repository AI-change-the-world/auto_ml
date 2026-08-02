from __future__ import annotations

import asyncio
import hashlib
import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from contracts import (
    DATASET_SOURCE_PROTOCOL_VERSION,
    MODEL_PACKAGE_PROTOCOL_VERSION,
    S3ObjectReference,
    StorageBucket,
    TrainingDatasetSourceManifest,
)
from registry import PackageRegistryError, TrainingPackageRegistry
from storage import DatasetMaterializer, ModelInputMaterializer, ObjectStorageError, content_reference


class MemoryObjectStorage:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    async def read(self, reference: S3ObjectReference) -> bytes:
        key = (reference.bucket.value, reference.object_key)
        if key not in self.objects:
            raise ObjectStorageError(f"missing {key}")
        value = self.objects[key]
        if reference.sha256 and hashlib.sha256(value).hexdigest() != reference.sha256:
            raise ObjectStorageError("object SHA-256 mismatch")
        if reference.size_bytes is not None and len(value) != reference.size_bytes:
            raise ObjectStorageError("object size mismatch")
        return value

    async def write(self, reference: S3ObjectReference, content: bytes) -> None:
        if reference.sha256 and hashlib.sha256(content).hexdigest() != reference.sha256:
            raise ObjectStorageError("object SHA-256 mismatch")
        self.objects[(reference.bucket.value, reference.object_key)] = content

    async def exists(self, reference: S3ObjectReference) -> bool:
        return (reference.bucket.value, reference.object_key) in self.objects


def package_archive(version: str = "1.0.0") -> bytes:
    manifest = {
        "protocol_version": "training-code-package/v1",
        "key": "registry-test-package",
        "version": version,
        "name": "Registry Test Package",
        "runtime": {"id": "pytorch-2.5-cu124"},
        "entrypoint": "train.py",
        "supported_tasks": [{"task_kind": "classification", "data_modalities": ["image"], "annotation_kinds": []}],
        "parameters_schema": {"type": "object", "properties": {}},
        "model_input_contract": {
            "framework": {"id": "pytorch", "version": "2.5"},
            "formats": ["pt"],
            "modes": ["initialize", "resume"],
        },
        "output_contract": {"artifacts": [{"role": "model", "formats": ["onnx"], "deployable": True}]},
    }
    archive = BytesIO()
    with ZipFile(archive, "w") as bundle:
        bundle.writestr("training_package.json", json.dumps(manifest))
        bundle.writestr("train.py", "def train(context, report): return {}\n")
    return archive.getvalue()


def model_package_archive(*, include_resume_checkpoint: bool = True) -> bytes:
    manifest = {
        "protocol_version": MODEL_PACKAGE_PROTOCOL_VERSION,
        "name": "Imported Classifier",
        "task_kind": "classification",
        "class_names": ["cat", "dog"],
        "framework": {"id": "pytorch", "version": "2.5"},
        "artifact_path": "weights/model.pt",
        "format": "pt",
        "metadata": {"architecture": "resnet18"},
    }
    if include_resume_checkpoint:
        manifest["resume_checkpoint_path"] = "checkpoints/last.pt"
    archive = BytesIO()
    with ZipFile(archive, "w") as bundle:
        bundle.writestr("training_model_package.json", json.dumps(manifest))
        bundle.writestr("weights/model.pt", b"inference weights")
        if include_resume_checkpoint:
            bundle.writestr("checkpoints/last.pt", b"resumable checkpoint")
    return archive.getvalue()


class TrainingRegistryTest(unittest.TestCase):
    def test_registers_immutable_package_and_reuses_same_digest(self) -> None:
        storage = MemoryObjectStorage()
        registry = TrainingPackageRegistry(storage)
        archive = package_archive()

        first = asyncio.run(registry.register_package(archive_name="classifier.zip", archive_bytes=archive))
        repeated = asyncio.run(registry.register_package(archive_name="classifier.zip", archive_bytes=archive))

        self.assertTrue(first.created)
        self.assertFalse(repeated.created)
        self.assertEqual(first.registration.archive.sha256, repeated.registration.archive.sha256)
        self.assertIn(
            ("default", first.registration.archive.object_key),
            storage.objects,
        )

    def test_rejects_different_archive_under_same_key_and_version(self) -> None:
        storage = MemoryObjectStorage()
        registry = TrainingPackageRegistry(storage)
        asyncio.run(registry.register_package(archive_name="first.zip", archive_bytes=package_archive()))
        with self.assertRaises(PackageRegistryError):
            asyncio.run(
                registry.register_package(
                    archive_name="second.zip",
                    archive_bytes=package_archive() + b"different-bytes",
                )
            )

    def test_registers_model_package_with_distinct_initialize_and_resume_inputs(self) -> None:
        storage = MemoryObjectStorage()
        registry = TrainingPackageRegistry(storage)
        outcome = asyncio.run(
            registry.register_model_package(
                archive_name="classifier-model.zip",
                archive_bytes=model_package_archive(),
            )
        )
        registration = outcome.registration
        self.assertTrue(outcome.created)
        self.assertEqual(registration.initialize_artifact.object.bucket, StorageBucket.MODELS)
        self.assertEqual(registration.initialize_artifact.source, "uploaded_model_package")
        self.assertFalse(registration.initialize_artifact.resume_supported)
        self.assertIsNotNone(registration.resume_artifact)
        self.assertTrue(registration.resume_artifact.resume_supported)
        self.assertNotEqual(
            registration.initialize_artifact.object.object_key,
            registration.resume_artifact.object.object_key,
        )
        self.assertIn(("models", registration.archive.object_key), storage.objects)

        repeated = asyncio.run(
            registry.register_model_package(
                archive_name="classifier-model.zip",
                archive_bytes=model_package_archive(),
            )
        )
        self.assertFalse(repeated.created)

    def test_registers_dataset_snapshot_and_materializes_model_input(self) -> None:
        storage = MemoryObjectStorage()
        registry = TrainingPackageRegistry(storage)
        image = b"image bytes"
        image_ref = content_reference(StorageBucket.DATASETS, "datasets/cat.jpg", image)
        asyncio.run(storage.write(image_ref, image))
        source_manifest = TrainingDatasetSourceManifest(
            protocol_version=DATASET_SOURCE_PROTOCOL_VERSION,
            task_kind="classification",
            data_modalities=["image"],
            annotation_kinds=["classification"],
            class_names=["cat", "dog"],
            items=[{"item_id": "cat-1", "split": "train", "media": image_ref}],
        )
        snapshot = asyncio.run(registry.register_dataset_snapshot(source_manifest))
        self.assertEqual(snapshot.object.bucket, StorageBucket.DEFAULT)
        self.assertIn(("default", snapshot.object.object_key), storage.objects)
        self.assertEqual(snapshot.source_manifest.items[0].media.sha256, image_ref.sha256)
        self.assertEqual(snapshot.source_manifest.items[0].media.size_bytes, len(image))

        model_ref = content_reference(StorageBucket.MODELS, "models/imported.pt", b"model")
        asyncio.run(storage.write(model_ref, b"model"))
        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = asyncio.run(
                ModelInputMaterializer(storage).materialize(model_ref, Path(temp_dir), file_name="imported.pt")
            )
            self.assertEqual(local_path.read_bytes(), b"model")
            self.assertEqual(local_path.relative_to(temp_dir).as_posix(), "model-input/imported.pt")

    def test_materializes_existing_dataset_and_annotation_s3_objects(self) -> None:
        storage = MemoryObjectStorage()
        image = b"image bytes"
        annotation = b'{"class": "cat"}'
        image_ref = content_reference(StorageBucket.DATASETS, "datasets/cat.jpg", image)
        annotation_ref = content_reference(StorageBucket.ANNOTATIONS, "annotations/cat.json", annotation)
        asyncio.run(storage.write(image_ref, image))
        asyncio.run(storage.write(annotation_ref, annotation))
        source_manifest = TrainingDatasetSourceManifest(
            protocol_version=DATASET_SOURCE_PROTOCOL_VERSION,
            task_kind="classification",
            data_modalities=["image"],
            annotation_kinds=["classification"],
            class_names=["cat", "dog"],
            items=[{"item_id": "cat-1", "split": "train", "media": image_ref, "annotation": annotation_ref}],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            materialized = asyncio.run(DatasetMaterializer(storage).materialize(source_manifest, Path(temp_dir)))
            self.assertEqual(materialized.items[0].media_path, "dataset/00000000_cat-1/cat.jpg")
            self.assertEqual((Path(temp_dir) / materialized.items[0].media_path).read_bytes(), image)
            self.assertEqual((Path(temp_dir) / materialized.items[0].annotation_path).read_bytes(), annotation)
            self.assertTrue((Path(temp_dir) / "dataset-manifest.json").is_file())
