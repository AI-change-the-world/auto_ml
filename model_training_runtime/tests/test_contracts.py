from __future__ import annotations

import unittest
import tempfile
from uuid import uuid4
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import json
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import app, require_registration_authorization


PACKAGE_SHA256 = "a" * 64
DATASET_SHA256 = "b" * 64


def package_manifest() -> dict:
    return {
        "protocol_version": "training-code-package/v1",
        "key": "pytorch-image-classifier",
        "version": "1.0.0",
        "name": "PyTorch Image Classifier",
        "runtime": {"id": "pytorch-2.5-cu124"},
        "entrypoint": "train.py",
        "supported_tasks": [
            {
                "task_kind": "classification",
                "data_modalities": ["image"],
                "annotation_kinds": ["classification"],
            }
        ],
        "parameters_schema": {
            "type": "object",
            "properties": {"epochs": {"type": "integer", "minimum": 1}},
            "required": ["epochs"],
            "additionalProperties": False,
        },
        "model_input_contract": {
            "framework": {"id": "pytorch", "version": "2.5"},
            "formats": ["pt"],
            "modes": ["initialize", "resume"],
        },
        "output_contract": {
            "artifacts": [{"role": "model", "formats": ["onnx"], "deployable": True}],
        },
    }


def dataset_manifest() -> dict:
    return {
        "protocol_version": "training-dataset-manifest/v1",
        "task_kind": "classification",
        "data_modalities": ["image"],
        "annotation_kinds": ["classification"],
        "class_names": ["cat", "dog"],
        "items": [
            {
                "item_id": "sample-1",
                "split": "train",
                "media_path": "images/sample-1.jpg",
                "annotation_path": "labels/sample-1.json",
            }
        ],
    }


def execution_request() -> dict:
    execution_id = str(uuid4())
    return {
        "protocol_version": "training-execution/v1",
        "execution_id": execution_id,
        "task": {"task_id": 1, "task_kind": "classification"},
        "package": {"key": "pytorch-image-classifier", "version": "1.0.0", "sha256": PACKAGE_SHA256},
        "runtime": {"id": "pytorch-2.5-cu124"},
        "workspace": {
            "root_dir": "/workspace",
            "code_dir": "/workspace/code",
            "input_dir": "/workspace/input",
            "output_dir": "/workspace/output",
            "dataset_manifest_path": "/workspace/input/dataset-manifest.json",
        },
        "dataset": dataset_manifest(),
        "parameters": {"epochs": 3},
        "resources": {"device": "cuda", "gpu_count": 1, "cpu_cores": 4, "memory_bytes": 8589934592, "timeout_seconds": 3600},
    }


def model_input(*, mode: str = "initialize", resume_supported: bool = False) -> dict:
    return {
        "mode": mode,
        "artifact": {
            "source": "uploaded_model_package",
            "object": {
                "bucket": "models",
                "object_key": "training-code-runtime/model-packages/a/model.pt",
                "sha256": "c" * 64,
                "size_bytes": 1024,
            },
            "format": "pt",
            "task_kind": "classification",
            "class_names": ["cat", "dog"],
            "display_name": "Imported classifier",
            "framework": {"id": "pytorch", "version": "2.5"},
            "resume_supported": resume_supported,
        },
    }


def successful_result(execution_id: str) -> dict:
    return {
        "protocol_version": "training-result/v1",
        "execution_id": execution_id,
        "status": "succeeded",
        "metrics": {"accuracy": 0.93},
        "artifacts": [
            {
                "path": "model.onnx",
                "role": "model",
                "format": "onnx",
                "size_bytes": 1024,
                "deployable": True,
            }
        ],
        "model": {
            "task_kind": "classification",
            "class_names": ["cat", "dog"],
            "framework": {"id": "pytorch", "version": "2.5"},
        },
    }


class ContractApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_health_marks_service_as_contract_only(self) -> None:
        with patch("app.load_model_training_runtime_config", return_value={}):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "contract_validation_only")
        self.assertFalse(response.json()["execution_enabled"])

    def test_lists_model_package_protocol(self) -> None:
        response = self.client.get("/v1/contracts")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["contracts"]["model_package"],
            "training-model-package/v1",
        )

    def test_runs_registered_submission_through_in_service_execution_endpoint(self) -> None:
        execution_id = str(uuid4())
        submission = {
            "protocol_version": "training-code-submit/v1",
            "message_id": str(uuid4()),
            "execution_id": execution_id,
            "task": {"task_id": 1, "task_kind": "classification"},
            "package": {
                "key": "pytorch-image-classifier",
                "version": "1.0.0",
                "sha256": PACKAGE_SHA256,
            },
            "package_archive": {
                "bucket": "default",
                "object_key": "training-packages/classifier.zip",
                "sha256": PACKAGE_SHA256,
                "size_bytes": 1024,
            },
            "dataset_source_snapshot": {
                "bucket": "default",
                "object_key": "training-inputs/1.json",
                "sha256": DATASET_SHA256,
                "size_bytes": 1024,
            },
            "runtime": {"id": "python-host"},
            "resources": {"device": "cpu", "gpu_count": 0},
        }
        result = {
            "protocol_version": "training-result/v1",
            "execution_id": execution_id,
            "status": "succeeded",
            "metrics": {"accuracy": 0.91},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir) / "workspaces"
            workspace_root.mkdir()
            (workspace_root / execution_id).mkdir()
            fake_coordinator = SimpleNamespace(
                runtime_manager=SimpleNamespace(settings=SimpleNamespace(workspace_root=workspace_root)),
                execute=lambda _: None,
            )

            async def execute(_submission):
                return SimpleNamespace(
                    execution=SimpleNamespace(execution_id=execution_id),
                    result=result,
                    events=({"event_type": "phase", "phase": "prepare"},),
                    logs=({"level": "info", "message": "started"},),
                )

            fake_coordinator.execute = execute
            with patch("app.get_training_coordinator", return_value=(fake_coordinator, workspace_root)):
                with patch("app.load_model_training_runtime_config", return_value={}):
                    response = self.client.post("/v1/executions/run", json=submission)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"]["status"], "succeeded")
        self.assertEqual(response.json()["events"][0]["phase"], "prepare")
        self.assertTrue(response.json()["workspace_cleaned"])

    def test_registration_token_is_optional_locally_and_required_when_configured(self) -> None:
        with patch("app.load_model_training_runtime_config", return_value={}):
            require_registration_authorization()

        with patch("app.load_model_training_runtime_config", return_value={"token": "runtime-token"}):
            with self.assertRaises(HTTPException) as missing:
                require_registration_authorization()
            self.assertEqual(missing.exception.status_code, 401)

            with self.assertRaises(HTTPException):
                require_registration_authorization("Bearer wrong-token")
            require_registration_authorization("Bearer runtime-token")

    def test_accepts_valid_package_contract(self) -> None:
        response = self.client.post("/v1/contracts/package/validate", json=package_manifest())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])
        self.assertEqual(response.json()["normalized"]["key"], "pytorch-image-classifier")

    def test_rejects_unsafe_package_entrypoint(self) -> None:
        payload = package_manifest()
        payload["entrypoint"] = "../train.py"
        response = self.client.post("/v1/contracts/package/validate", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_validates_zip_layout_without_executing_user_code(self) -> None:
        archive = BytesIO()
        with ZipFile(archive, "w") as bundle:
            bundle.writestr("training_package.json", json.dumps(package_manifest()))
            bundle.writestr("train.py", "raise RuntimeError('this must not run during validation')\n")
        response = self.client.post(
            "/v1/packages/archive/validate",
            content=archive.getvalue(),
            headers={"content-type": "application/zip"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])
        self.assertEqual(response.json()["manifest"]["entrypoint"], "train.py")

    def test_inspects_training_package_configuration_without_returning_source(self) -> None:
        archive = BytesIO()
        with ZipFile(archive, "w") as bundle:
            bundle.writestr("training_package.json", json.dumps(package_manifest()))
            bundle.writestr("train.py", "SOURCE_CONTENT_MUST_NOT_BE_RETURNED\n")
        response = self.client.post(
            "/v1/packages/archive/inspect",
            content=archive.getvalue(),
            headers={"content-type": "application/zip"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["kind"], "training_code_package")
        self.assertTrue(body["valid"])
        self.assertEqual(body["configuration"]["key"], "pytorch-image-classifier")
        self.assertEqual(body["configuration"]["parameters_schema"], package_manifest()["parameters_schema"])
        self.assertIn("sha256", body["archive"])
        self.assertNotIn("SOURCE_CONTENT_MUST_NOT_BE_RETURNED", response.text)

    def test_validates_model_package_zip_without_loading_model_bytes(self) -> None:
        model_manifest = {
            "protocol_version": "training-model-package/v1",
            "name": "Imported classifier",
            "task_kind": "classification",
            "class_names": ["cat", "dog"],
            "framework": {"id": "pytorch", "version": "2.5"},
            "artifact_path": "weights/model.pt",
            "resume_checkpoint_path": "checkpoints/last.pt",
            "format": "pt",
        }
        archive = BytesIO()
        with ZipFile(archive, "w") as bundle:
            bundle.writestr("training_model_package.json", json.dumps(model_manifest))
            bundle.writestr("weights/model.pt", b"not deserialized")
            bundle.writestr("checkpoints/last.pt", b"not deserialized")
        response = self.client.post(
            "/v1/model-packages/archive/validate",
            content=archive.getvalue(),
            headers={"content-type": "application/zip"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["manifest"]["artifact_path"], "weights/model.pt")

        missing_member = BytesIO()
        with ZipFile(missing_member, "w") as bundle:
            bundle.writestr("training_model_package.json", json.dumps(model_manifest))
            bundle.writestr("weights/model.pt", b"not deserialized")
        response = self.client.post(
            "/v1/model-packages/archive/validate",
            content=missing_member.getvalue(),
            headers={"content-type": "application/zip"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("missing regular file", response.json()["detail"])

    def test_inspects_model_package_configuration_without_returning_weight_bytes(self) -> None:
        model_manifest = {
            "protocol_version": "training-model-package/v1",
            "name": "Imported classifier",
            "task_kind": "classification",
            "class_names": ["cat", "dog"],
            "framework": {"id": "pytorch", "version": "2.5"},
            "artifact_path": "weights/model.pt",
            "resume_checkpoint_path": "checkpoints/last.pt",
            "format": "pt",
            "metadata": {"architecture": "resnet18"},
        }
        archive = BytesIO()
        with ZipFile(archive, "w") as bundle:
            bundle.writestr("training_model_package.json", json.dumps(model_manifest))
            bundle.writestr("weights/model.pt", b"MODEL_BYTES_MUST_NOT_BE_RETURNED")
            bundle.writestr("checkpoints/last.pt", b"CHECKPOINT_BYTES_MUST_NOT_BE_RETURNED")
        response = self.client.post(
            "/v1/model-packages/archive/inspect",
            content=archive.getvalue(),
            headers={"content-type": "application/zip"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["kind"], "training_model_package")
        self.assertEqual(body["configuration"]["framework"]["id"], "pytorch")
        self.assertEqual(body["configuration"]["resume_checkpoint_path"], "checkpoints/last.pt")
        self.assertEqual(body["configuration"]["metadata"], {"architecture": "resnet18"})
        self.assertNotIn("MODEL_BYTES_MUST_NOT_BE_RETURNED", response.text)
        self.assertNotIn("CHECKPOINT_BYTES_MUST_NOT_BE_RETURNED", response.text)

    def test_inspection_rejects_invalid_archive(self) -> None:
        response = self.client.post(
            "/v1/packages/archive/inspect",
            content=b"not-a-zip",
            headers={"content-type": "application/zip"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("valid ZIP", response.json()["detail"])

    def test_rejects_zip_path_traversal(self) -> None:
        archive = BytesIO()
        with ZipFile(archive, "w") as bundle:
            bundle.writestr("training_package.json", json.dumps(package_manifest()))
            bundle.writestr("../train.py", "pass\n")
        response = self.client.post(
            "/v1/packages/archive/validate",
            content=archive.getvalue(),
            headers={"content-type": "application/zip"},
        )
        self.assertEqual(response.status_code, 422)

    def test_rejects_package_managed_dependency_file(self) -> None:
        archive = BytesIO()
        with ZipFile(archive, "w") as bundle:
            bundle.writestr("training_package.json", json.dumps(package_manifest()))
            bundle.writestr("train.py", "pass\n")
            bundle.writestr("requirements.txt", "torch\n")
        response = self.client.post(
            "/v1/packages/archive/validate",
            content=archive.getvalue(),
            headers={"content-type": "application/zip"},
        )
        self.assertEqual(response.status_code, 422)

    def test_accepts_execution_event_and_result_contracts(self) -> None:
        execution = execution_request()
        execution_id = execution["execution_id"]
        response = self.client.post("/v1/contracts/execution/validate", json=execution)
        self.assertEqual(response.status_code, 200)

        event = {
            "protocol_version": "training-event/v1",
            "execution_id": execution_id,
            "sequence": 1,
            "occurred_at": "2026-08-02T00:00:00Z",
            "event_type": "metric",
            "split": "val",
            "epoch": 1,
            "metrics": {"accuracy": 0.93},
        }
        response = self.client.post("/v1/contracts/event/validate", json=event)
        self.assertEqual(response.status_code, 200)

        result = successful_result(execution_id)
        response = self.client.post("/v1/contracts/result/validate", json=result)
        self.assertEqual(response.status_code, 200)

    def test_admits_compatible_package_execution_and_result(self) -> None:
        execution = execution_request()
        request = {"manifest": package_manifest(), "execution": execution}
        response = self.client.post("/v1/admission/execution/validate", json=request)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/v1/admission/result/validate",
            json={**request, "result": successful_result(execution["execution_id"])},
        )
        self.assertEqual(response.status_code, 200)

    def test_admits_model_package_inputs_and_requires_real_resume_checkpoint(self) -> None:
        execution = execution_request()
        execution["model_input"] = model_input()
        execution["model_input_path"] = "/workspace/input/model-input/model.pt"
        response = self.client.post(
            "/v1/admission/execution/validate",
            json={"manifest": package_manifest(), "execution": execution},
        )
        self.assertEqual(response.status_code, 200)

        execution["model_input"] = model_input(mode="resume")
        response = self.client.post(
            "/v1/admission/execution/validate",
            json={"manifest": package_manifest(), "execution": execution},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("resumable checkpoint", response.json()["detail"])

        execution["model_input"] = model_input(mode="resume", resume_supported=True)
        response = self.client.post(
            "/v1/admission/execution/validate",
            json={"manifest": package_manifest(), "execution": execution},
        )
        self.assertEqual(response.status_code, 200)

        execution["model_input"]["artifact"]["framework"]["version"] = "2.4"
        response = self.client.post(
            "/v1/admission/execution/validate",
            json={"manifest": package_manifest(), "execution": execution},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("framework", response.json()["detail"])

    def test_rejects_parameters_task_and_output_contract_mismatches(self) -> None:
        execution = execution_request()
        request = {"manifest": package_manifest(), "execution": execution}

        request["execution"]["parameters"] = {"epochs": 0}
        response = self.client.post("/v1/admission/execution/validate", json=request)
        self.assertEqual(response.status_code, 422)
        self.assertIn("$parameters.epochs", response.json()["detail"])

        request = {"manifest": package_manifest(), "execution": execution_request()}
        request["execution"]["dataset"]["annotation_kinds"] = ["detection"]
        response = self.client.post("/v1/admission/execution/validate", json=request)
        self.assertEqual(response.status_code, 422)
        self.assertIn("annotation_kinds", response.json()["detail"])

        request = {"manifest": package_manifest(), "execution": execution_request()}
        invalid_result = successful_result(request["execution"]["execution_id"])
        invalid_result["artifacts"][0]["format"] = "pt"
        response = self.client.post(
            "/v1/admission/result/validate",
            json={**request, "result": invalid_result},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("format `pt`", response.json()["detail"])

    def test_rejects_result_resume_pointer_without_checkpoint_artifact(self) -> None:
        execution = execution_request()
        result = successful_result(execution["execution_id"])
        result["model"]["resume_checkpoint_path"] = "last.pt"
        response = self.client.post(
            "/v1/admission/result/validate",
            json={"manifest": package_manifest(), "execution": execution, "result": result},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("resume_checkpoint_path", response.json()["detail"])

    def test_accepts_result_resume_pointer_to_checkpoint_artifact(self) -> None:
        manifest = package_manifest()
        manifest["output_contract"]["artifacts"].append(
            {"role": "checkpoint", "formats": ["pt"], "required": False}
        )
        execution = execution_request()
        result = successful_result(execution["execution_id"])
        result["artifacts"].append(
            {
                "path": "checkpoints/last.pt",
                "role": "checkpoint",
                "format": "pt",
                "size_bytes": 2048,
            }
        )
        result["model"]["resume_checkpoint_path"] = "checkpoints/last.pt"
        response = self.client.post(
            "/v1/admission/result/validate",
            json={"manifest": manifest, "execution": execution, "result": result},
        )
        self.assertEqual(response.status_code, 200)

    def test_rejects_shared_workspace_directories_and_invalid_package_schema(self) -> None:
        execution = execution_request()
        execution["workspace"]["output_dir"] = execution["workspace"]["input_dir"]
        response = self.client.post(
            "/v1/admission/execution/validate",
            json={"manifest": package_manifest(), "execution": execution},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("separate directories", response.json()["detail"])

        invalid_manifest = package_manifest()
        invalid_manifest["parameters_schema"] = {"type": "object", "properties": "not-an-object"}
        response = self.client.post("/v1/contracts/package/validate", json=invalid_manifest)
        self.assertEqual(response.status_code, 422)

    def test_rejects_invalid_metric_and_invalid_result_state(self) -> None:
        execution_id = str(uuid4())
        event = {
            "protocol_version": "training-event/v1",
            "execution_id": execution_id,
            "sequence": 1,
            "occurred_at": "2026-08-02T00:00:00Z",
            "event_type": "metric",
            "metrics": {},
        }
        response = self.client.post("/v1/contracts/event/validate", json=event)
        self.assertEqual(response.status_code, 422)

        result = {
            "protocol_version": "training-result/v1",
            "execution_id": execution_id,
            "status": "failed",
        }
        response = self.client.post("/v1/contracts/result/validate", json=result)
        self.assertEqual(response.status_code, 422)

    def test_accepts_reserved_mq_submission_contract(self) -> None:
        response = self.client.post(
            "/v1/contracts/mq-submission/validate",
            json={
                "protocol_version": "training-code-submit/v1",
                "message_id": str(uuid4()),
                "execution_id": str(uuid4()),
                "task": {"task_id": 1, "task_kind": "classification"},
                "package": {"key": "pytorch-image-classifier", "version": "1.0.0", "sha256": PACKAGE_SHA256},
                "package_archive": {
                    "bucket": "default",
                    "object_key": "training-packages/classifier.zip",
                    "sha256": PACKAGE_SHA256,
                    "size_bytes": 1024,
                },
                "dataset_source_snapshot": {
                    "bucket": "default",
                    "object_key": "training-inputs/1.json",
                    "sha256": DATASET_SHA256,
                    "size_bytes": 1024,
                },
                "runtime": {"id": "pytorch-2.5-cu124"},
                "resources": {"device": "cpu", "gpu_count": 0},
            },
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
