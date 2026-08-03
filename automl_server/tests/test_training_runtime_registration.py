"""Tests for the custom training runtime ZIP registration boundary."""
import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock


RUNTIME_MODULE_DIR = Path(__file__).resolve().parents[1] / "app" / "modules" / "training_runtime"
TASK_SCHEMAS_PATH = Path(__file__).resolve().parents[1] / "app" / "modules" / "task" / "schemas.py"
PACKAGE_NAME = "app.modules.training_runtime"
package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(RUNTIME_MODULE_DIR)]
sys.modules[PACKAGE_NAME] = package

SCHEMAS_SPEC = importlib.util.spec_from_file_location(
    f"{PACKAGE_NAME}.schemas",
    RUNTIME_MODULE_DIR / "schemas.py",
)
if SCHEMAS_SPEC is None or SCHEMAS_SPEC.loader is None:
    raise RuntimeError("unable to load training runtime schemas")
SCHEMAS_MODULE = importlib.util.module_from_spec(SCHEMAS_SPEC)
sys.modules[SCHEMAS_SPEC.name] = SCHEMAS_MODULE
SCHEMAS_SPEC.loader.exec_module(SCHEMAS_MODULE)

TASK_SCHEMAS_SPEC = importlib.util.spec_from_file_location(
    "runtime_task_schemas_test_module",
    TASK_SCHEMAS_PATH,
)
if TASK_SCHEMAS_SPEC is None or TASK_SCHEMAS_SPEC.loader is None:
    raise RuntimeError("unable to load task schemas")
TASK_SCHEMAS_MODULE = importlib.util.module_from_spec(TASK_SCHEMAS_SPEC)
sys.modules[TASK_SCHEMAS_SPEC.name] = TASK_SCHEMAS_MODULE
TASK_SCHEMAS_SPEC.loader.exec_module(TASK_SCHEMAS_MODULE)
RuntimeScriptTaskCreate = TASK_SCHEMAS_MODULE.RuntimeScriptTaskCreate


class _UnusedHttpClient:
    def __init__(self, *args, **kwargs) -> None:
        pass


http_client_module = types.ModuleType("app.utils.http_client")
http_client_module.HttpClient = _UnusedHttpClient
sys.modules["app.utils.http_client"] = http_client_module
REGISTRATION_SPEC = importlib.util.spec_from_file_location(
    f"{PACKAGE_NAME}.registration",
    RUNTIME_MODULE_DIR / "registration.py",
)
if REGISTRATION_SPEC is None or REGISTRATION_SPEC.loader is None:
    raise RuntimeError("unable to load training runtime registration boundary")
REGISTRATION_MODULE = importlib.util.module_from_spec(REGISTRATION_SPEC)
sys.modules[REGISTRATION_SPEC.name] = REGISTRATION_MODULE
REGISTRATION_SPEC.loader.exec_module(REGISTRATION_MODULE)
TrainingRuntimeRegistrar = REGISTRATION_MODULE.TrainingRuntimeRegistrar


def object_reference(bucket: str, object_key: str, digest: str, size_bytes: int) -> dict:
    return {
        "bucket": bucket,
        "object_key": object_key,
        "sha256": digest * 64,
        "size_bytes": size_bytes,
    }


class TrainingRuntimeRegistrarTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registrar = TrainingRuntimeRegistrar(
            base_url="http://model-training-runtime:8012",
            timeout=30,
            token="runtime-token",
        )
        self.registrar._client.post = AsyncMock()

    def test_registers_code_zip_only_through_runtime_catalog_endpoint(self) -> None:
        self.registrar._client.post.return_value = types.SimpleNamespace(
            status_code=200,
            json=lambda: {
                "created": True,
                "registration": {
                    "manifest": {
                        "protocol_version": "training-code-package/v1",
                        "key": "custom-trainer",
                        "version": "1.0.0",
                        "name": "Custom trainer",
                        "runtime": {"id": "python-host", "kind": "platform_managed"},
                        "entrypoint": "train.py",
                        "entrypoint_symbol": "train",
                        "supported_tasks": [{"task_kind": "classification"}],
                        "class_names": ["cat", "dog"],
                        "parameters_schema": {"type": "object", "properties": {}},
                        "output_contract": {"artifacts": []},
                    },
                    "archive": object_reference(
                        "default",
                        "training-code-runtime/packages/custom-trainer/1.0.0/source.zip",
                        "a",
                        123,
                    ),
                    "package_file_name": "custom-trainer.zip",
                },
            },
        )

        result = asyncio.run(
            self.registrar.register_code_package(
                archive_name="custom-trainer.zip",
                archive_bytes=b"zip-content",
            )
        )

        self.assertTrue(result.created)
        self.assertEqual(result.registration.manifest.key, "custom-trainer")
        self.assertEqual(result.registration.manifest.class_names, ["cat", "dog"])
        self.assertEqual(
            self.registrar._client.post.await_args.args[0],
            "/v1/registrations/packages",
        )
        self.assertEqual(
            self.registrar._client.post.await_args.kwargs["params"],
            {"archive_name": "custom-trainer.zip"},
        )
        self.assertEqual(
            self.registrar._client.post.await_args.kwargs["headers"],
            {"Content-Type": "application/zip", "Authorization": "Bearer runtime-token"},
        )

    def test_registers_model_zip_only_through_runtime_catalog_endpoint(self) -> None:
        self.registrar._client.post.return_value = types.SimpleNamespace(
            status_code=200,
            json=lambda: {
                "created": True,
                "registration": {
                    "manifest": {
                        "protocol_version": "training-model-package/v1",
                        "name": "Custom model",
                        "task_kind": "classification",
                        "class_names": ["cat", "dog"],
                        "framework": {"id": "pytorch", "version": "2.5"},
                        "artifact_path": "weights/model.pt",
                        "format": "pt",
                        "metadata": {},
                    },
                    "archive": object_reference(
                        "models",
                        "training-code-runtime/model-packages/a/source.zip",
                        "a",
                        456,
                    ),
                    "package_file_name": "custom-model.zip",
                    "initialize_artifact": {
                        "source": "uploaded_model_package",
                        "object": object_reference(
                            "models",
                            "training-code-runtime/model-packages/a/initialize.pt",
                            "b",
                            789,
                        ),
                        "format": "pt",
                        "task_kind": "classification",
                        "class_names": ["cat", "dog"],
                        "display_name": "Custom model",
                        "framework": {"id": "pytorch", "version": "2.5"},
                        "resume_supported": False,
                        "metadata": {},
                    },
                },
            },
        )

        result = asyncio.run(
            self.registrar.register_model_package(
                archive_name="custom-model.zip",
                archive_bytes=b"zip-content",
            )
        )

        self.assertTrue(result.created)
        self.assertEqual(result.registration.initialize_artifact.object.sha256, "b" * 64)
        self.assertEqual(
            self.registrar._client.post.await_args.args[0],
            "/v1/registrations/model-packages",
        )


class RuntimeScriptTaskRequestTest(unittest.TestCase):
    def test_allows_empty_annotation_kinds_for_script_managed_data(self) -> None:
        request = RuntimeScriptTaskCreate(
            code_package_id=1,
            task_type=1,
            input_mode="script_managed",
            class_names=["negative", "positive"],
            data_modalities=["image"],
            annotation_kinds=[],
        )

        self.assertEqual(request.annotation_kinds, [])


if __name__ == "__main__":
    unittest.main()
