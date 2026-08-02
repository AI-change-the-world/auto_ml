from __future__ import annotations

import unittest
from uuid import uuid4
from io import BytesIO
from zipfile import ZipFile
import json

from fastapi.testclient import TestClient

from app import app


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
        "parameters_schema": {"type": "object", "properties": {"epochs": {"type": "integer"}}},
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


class ContractApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_health_marks_service_as_contract_only(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "contract_validation_only")
        self.assertFalse(response.json()["execution_enabled"])

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

        result = {
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
            "model": {"task_kind": "classification", "class_names": ["cat", "dog"]},
        }
        response = self.client.post("/v1/contracts/result/validate", json=result)
        self.assertEqual(response.status_code, 200)

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
                "package_archive": {"object_key": "training-packages/classifier.zip", "sha256": PACKAGE_SHA256},
                "dataset_manifest": {"object_key": "training-inputs/1.json", "sha256": DATASET_SHA256},
                "runtime": {"id": "pytorch-2.5-cu124"},
                "resources": {"device": "cpu", "gpu_count": 0},
            },
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
