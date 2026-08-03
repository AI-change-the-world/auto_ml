from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from contracts import (
    DATASET_SOURCE_PROTOCOL_VERSION,
    SUBMISSION_PROTOCOL_VERSION,
    S3ObjectReference,
    StorageBucket,
    TrainingCodeSubmission,
    TrainingDatasetSourceManifest,
)
from coordinator import ExecutionCoordinator, ExecutionCoordinatorError
from registry import TrainingPackageRegistry
from runtime import (
    ExecutionLaunch,
    LocalSubprocessExecutor,
    ManagedRuntimeSpec,
    PlatformRuntimeManager,
    ProcessResult,
    RuntimeExecutionSettings,
)
from storage import ObjectStorageError, content_reference


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
        self.objects[(reference.bucket.value, reference.object_key)] = content

    async def exists(self, reference: S3ObjectReference) -> bool:
        return (reference.bucket.value, reference.object_key) in self.objects


class RecordingExecutor:
    """Proves coordinator execution is decoupled from the local executor type."""

    supported_devices = frozenset({"cpu"})

    def __init__(self) -> None:
        self.launch: ExecutionLaunch | None = None
        self.delegate = LocalSubprocessExecutor()

    async def execute(self, launch: ExecutionLaunch, *, line_callback=None) -> ProcessResult:
        self.launch = launch
        return await self.delegate.execute(launch, line_callback=line_callback)


def package_archive(
    *,
    invalid_event: bool = False,
    malformed_protocol: bool = False,
    accepts_model_input: bool = False,
    bundled_weight: bool = False,
) -> bytes:
    manifest = {
        "protocol_version": "training-code-package/v1",
        "key": "coordinator-test-package",
        "version": "1.0.0",
        "name": "Coordinator Test Package",
        "runtime": {"id": "python-test-runtime"},
        "entrypoint": "train.py",
        "supported_tasks": [
            {"task_kind": "classification", "data_modalities": ["image"], "annotation_kinds": []}
        ],
        "parameters_schema": {
            "type": "object",
            "properties": {"epochs": {"type": "integer", "minimum": 1}},
            "required": ["epochs"],
        },
        "output_contract": {
            "artifacts": [{"role": "model", "formats": ["onnx"], "deployable": True}],
            "requires_model_metadata": True,
        },
    }
    event_line = (
        "report(event_type='phase', phase='prepare', sequence=99)"
    if invalid_event
        else "report(event_type='phase', phase='prepare', message='materialized input is ready')"
    )
    if accepts_model_input:
        manifest["model_input_contract"] = {
            "framework": {"id": "pytorch", "version": "2.5"},
            "formats": ["pt"],
            "modes": ["initialize"],
        }
    train = "\n".join(
        [
            "from pathlib import Path",
            "def train(context, report):",
            "    print('__AUTO_ML_TRAINING_EVENT__=not-json')" if malformed_protocol else "    pass",
            f"    {event_line}",
            "    assert (Path(__file__).parent / 'weights' / 'initial.pt').read_bytes() == b'bundled initial weights'" if bundled_weight else "    pass",
            "    Path(context['workspace']['output_dir'], 'model.onnx').write_bytes(b'model')",
            "    return {",
            "        'summary': 'completed',",
            "        'metrics': {'loss': 0.25},",
            "        'artifacts': [{'path': 'model.onnx', 'role': 'model', 'format': 'onnx', 'deployable': True}],",
            "        'model': {",
            "            'task_kind': context['task']['task_kind'],",
            "            'class_names': context['dataset']['class_names'],",
            "            'framework': {'id': 'pytorch', 'version': '2.5'},",
            "        },",
            "    }",
            "",
        ]
    )
    archive = BytesIO()
    with ZipFile(archive, "w") as bundle:
        bundle.writestr("training_package.json", json.dumps(manifest))
        bundle.writestr("train.py", train)
        if bundled_weight:
            bundle.writestr("weights/initial.pt", b"bundled initial weights")
    return archive.getvalue()


class ExecutionCoordinatorTest(unittest.TestCase):
    def _coordinator(
        self,
        storage: MemoryObjectStorage,
        workspace_root: Path,
        *,
        executor=None,
    ) -> ExecutionCoordinator:
        runtime_manager = PlatformRuntimeManager(
            RuntimeExecutionSettings(
                workspace_root=workspace_root,
                idle_timeout_seconds=5,
                max_output_bytes=16 * 1024,
            ),
            [
                ManagedRuntimeSpec(
                    runtime_id="python-test-runtime",
                    python_executable=Path(sys.executable),
                )
            ],
        )
        return ExecutionCoordinator(storage, runtime_manager, executor=executor)

    def _submission(
        self,
        storage: MemoryObjectStorage,
        *,
        invalid_event: bool = False,
        malformed_protocol: bool = False,
        include_model_input: bool = False,
        bundled_weight: bool = False,
    ) -> TrainingCodeSubmission:
        registry = TrainingPackageRegistry(storage)
        package = asyncio.run(
            registry.register_package(
                archive_name="coordinator-test.zip",
                archive_bytes=package_archive(
                    invalid_event=invalid_event,
                    malformed_protocol=malformed_protocol,
                    accepts_model_input=include_model_input,
                    bundled_weight=bundled_weight,
                ),
            )
        ).registration
        image = b"image"
        image_reference = content_reference(StorageBucket.DATASETS, "datasets/cat.jpg", image)
        asyncio.run(storage.write(image_reference, image))
        source = TrainingDatasetSourceManifest(
            protocol_version=DATASET_SOURCE_PROTOCOL_VERSION,
            task_kind="classification",
            data_modalities=["image"],
            annotation_kinds=[],
            class_names=["cat", "dog"],
            items=[{"item_id": "cat-1", "split": "train", "media": image_reference}],
        )
        snapshot = asyncio.run(registry.register_dataset_snapshot(source))
        model_input = None
        if include_model_input:
            weights = b"initial weights"
            weights_ref = content_reference(StorageBucket.MODELS, "models/initial.pt", weights)
            asyncio.run(storage.write(weights_ref, weights))
            model_input = {
                "mode": "initialize",
                "artifact": {
                    "source": "uploaded_model_package",
                    "object": weights_ref,
                    "format": "pt",
                    "task_kind": "classification",
                    "class_names": ["cat", "dog"],
                    "display_name": "Initial weights",
                    "framework": {"id": "pytorch", "version": "2.5"},
                },
            }
        return TrainingCodeSubmission(
            protocol_version=SUBMISSION_PROTOCOL_VERSION,
            message_id=uuid4(),
            execution_id=uuid4(),
            task={"task_id": 123, "task_kind": "classification"},
            package={
                "key": package.manifest.key,
                "version": package.manifest.version,
                "sha256": package.archive.sha256,
            },
            package_archive=package.archive,
            dataset_source_snapshot=snapshot.object,
            runtime=package.manifest.runtime,
            parameters={"epochs": 1},
            resources={"device": "cpu", "gpu_count": 0, "timeout_seconds": 15},
            model_input=model_input,
        )

    def test_runs_registered_package_from_pinned_inputs(self) -> None:
        storage = MemoryObjectStorage()
        submission = self._submission(storage)
        with tempfile.TemporaryDirectory() as temp_dir:
            outcome = asyncio.run(self._coordinator(storage, Path(temp_dir) / "workspaces").execute(submission))

            self.assertEqual(outcome.result.status, "succeeded")
            self.assertEqual(outcome.process.return_code, 0)
            self.assertEqual(outcome.execution.workspace.root_dir, "/workspace")
            self.assertEqual(len(outcome.events), 1)
            self.assertEqual(outcome.events[0]["sequence"], 0)
            self.assertTrue((outcome.workspace_root / "input" / "dataset-manifest.json").is_file())
            self.assertEqual((outcome.workspace_root / "output" / "model.onnx").read_bytes(), b"model")

    def test_returns_runner_structured_failure_for_bad_package_report(self) -> None:
        storage = MemoryObjectStorage()
        submission = self._submission(storage, invalid_event=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            outcome = asyncio.run(self._coordinator(storage, Path(temp_dir) / "workspaces").execute(submission))
        self.assertEqual(outcome.result.status, "failed")
        self.assertEqual(outcome.result.error.error_type, "TrainingRunnerError")
        self.assertEqual(outcome.process.return_code, 1)
        self.assertTrue(outcome.logs)

    def test_materializes_selected_model_input(self) -> None:
        storage = MemoryObjectStorage()
        submission = self._submission(storage, include_model_input=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            outcome = asyncio.run(self._coordinator(storage, Path(temp_dir) / "workspaces").execute(submission))
            model_path = outcome.workspace_root / "input" / "model-input" / "initial.pt"
            self.assertEqual(model_path.read_bytes(), b"initial weights")
        self.assertEqual(outcome.execution.model_input_path, "/workspace/input/model-input/initial.pt")

    def test_makes_bundled_weight_available_relative_to_script(self) -> None:
        storage = MemoryObjectStorage()
        submission = self._submission(storage, bundled_weight=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            outcome = asyncio.run(self._coordinator(storage, Path(temp_dir) / "workspaces").execute(submission))
            bundled_weight = outcome.workspace_root / "code" / "weights" / "initial.pt"
            self.assertEqual(bundled_weight.read_bytes(), b"bundled initial weights")
        self.assertEqual(outcome.result.status, "succeeded")

    def test_accepts_a_replaceable_executor(self) -> None:
        storage = MemoryObjectStorage()
        submission = self._submission(storage)
        executor = RecordingExecutor()
        with tempfile.TemporaryDirectory() as temp_dir:
            outcome = asyncio.run(
                self._coordinator(
                    storage,
                    Path(temp_dir) / "workspaces",
                    executor=executor,
                ).execute(submission)
            )
        self.assertEqual(outcome.result.status, "succeeded")
        self.assertIsNotNone(executor.launch)
        self.assertEqual(executor.launch.execution.execution_id, submission.execution_id)
        self.assertEqual(executor.launch.execution.workspace.root_dir, "/workspace")
        self.assertEqual(executor.launch.entrypoint_path.name, "train.py")

    def test_rejects_malformed_runner_protocol(self) -> None:
        storage = MemoryObjectStorage()
        submission = self._submission(storage, malformed_protocol=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ExecutionCoordinatorError) as raised:
                asyncio.run(self._coordinator(storage, Path(temp_dir) / "workspaces").execute(submission))
        self.assertEqual(raised.exception.error_detail["stage"], "parse_runner_output")
        self.assertEqual(raised.exception.error_detail["exception_type"], "RunnerProtocolError")

    def test_rejects_non_cpu_before_creating_workspace(self) -> None:
        storage = MemoryObjectStorage()
        submission = TrainingCodeSubmission.model_validate(
            {
                **self._submission(storage).model_dump(mode="json"),
                "resources": {"device": "cuda", "gpu_count": 1, "timeout_seconds": 15},
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir) / "workspaces"
            with self.assertRaises(ExecutionCoordinatorError) as raised:
                asyncio.run(self._coordinator(storage, workspace_root).execute(submission))
            self.assertFalse(workspace_root.exists())
        self.assertEqual(raised.exception.error_detail["exception_type"], "UnsupportedExecutorDevice")


if __name__ == "__main__":
    unittest.main()
