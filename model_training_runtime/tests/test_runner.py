from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from contracts import TrainingResult
from runner import EVENT_PREFIX, LOG_PREFIX, RESULT_PREFIX, TrainingRunnerError, _validate_output_contract


RUNNER_PATH = Path(__file__).resolve().parents[1] / "runner.py"


def execution_context(output_dir: Path) -> dict:
    return {
        "execution_id": str(uuid4()),
        "task": {"task_id": 1, "task_kind": "classification"},
        "workspace": {"output_dir": str(output_dir)},
        "dataset": {"class_names": ["cat", "dog"], "items": []},
        "parameters": {"epochs": 2},
    }


def package_manifest() -> dict:
    return {
        "protocol_version": "training-code-package/v1",
        "key": "runner-test-package",
        "version": "1.0.0",
        "name": "Runner Test Package",
        "runtime": {"id": "python-test-runtime"},
        "entrypoint": "train.py",
        "supported_tasks": [{"task_kind": "classification", "data_modalities": ["image"], "annotation_kinds": []}],
        "parameters_schema": {"type": "object", "properties": {"epochs": {"type": "integer"}}},
        "output_contract": {"artifacts": [{"role": "model", "formats": ["onnx"], "deployable": True}]},
    }


class TrainingRunnerTest(unittest.TestCase):
    def test_runs_template_and_enriches_result(self) -> None:
        template_dir = Path(__file__).resolve().parents[1] / "templates" / "training-package"
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            output_dir = workspace / "output"
            context_path = workspace / "execution.json"
            context_path.write_text(json.dumps(execution_context(output_dir)), encoding="utf-8")

            process = subprocess.run(
                [sys.executable, str(RUNNER_PATH), str(template_dir / "train.py"), str(context_path)],
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(process.returncode, 0, process.stderr)
            event_lines = [line for line in process.stdout.splitlines() if line.startswith(EVENT_PREFIX)]
            result_lines = [line for line in process.stdout.splitlines() if line.startswith(RESULT_PREFIX)]
            self.assertEqual(len(event_lines), 4)
            self.assertEqual(len(result_lines), 1)

            result = TrainingResult.model_validate_json((output_dir / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(result.status, "succeeded")
            self.assertEqual(result.artifacts[0].path, "model.onnx")
            self.assertEqual(result.artifacts[0].size_bytes, len(b"replace-with-exported-model"))
            self.assertEqual(result.artifacts[0].sha256, json.loads(result_lines[0][len(RESULT_PREFIX):])["artifacts"][0]["sha256"])

    def test_returns_structured_failure_for_bad_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            script_path = workspace / "train.py"
            script_path.write_text(
                "def train(context, report):\n"
                "    report(event_type='phase', phase='prepare', sequence=3)\n"
                "    return {}\n",
                encoding="utf-8",
            )
            output_dir = workspace / "output"
            context_path = workspace / "execution.json"
            context_path.write_text(json.dumps(execution_context(output_dir)), encoding="utf-8")

            process = subprocess.run(
                [sys.executable, str(RUNNER_PATH), str(script_path), str(context_path)],
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(process.returncode, 1)
            self.assertTrue(any(line.startswith(LOG_PREFIX) for line in process.stdout.splitlines()))
            result_line = next(line for line in process.stdout.splitlines() if line.startswith(RESULT_PREFIX))
            result = TrainingResult.model_validate(json.loads(result_line[len(RESULT_PREFIX):]))
            self.assertEqual(result.status, "failed")
            self.assertEqual(result.error.error_type, "TrainingRunnerError")

    def test_applies_manifest_output_contract_when_context_includes_it(self) -> None:
        execution_id = str(uuid4())
        context = {
            "protocol_version": "training-execution/v1",
            "execution_id": execution_id,
            "task": {"task_id": 1, "task_kind": "classification"},
            "package": {"key": "runner-test-package", "version": "1.0.0", "sha256": "a" * 64},
            "runtime": {"id": "python-test-runtime"},
            "workspace": {
                "root_dir": "/workspace",
                "code_dir": "/workspace/code",
                "input_dir": "/workspace/input",
                "output_dir": "/workspace/output",
                "dataset_manifest_path": "/workspace/input/dataset-manifest.json",
            },
            "dataset": {
                "protocol_version": "training-dataset-manifest/v1",
                "task_kind": "classification",
                "data_modalities": ["image"],
                "annotation_kinds": [],
                "class_names": ["cat", "dog"],
                "items": [{"item_id": "sample-1", "media_path": "images/sample-1.jpg"}],
            },
            "parameters": {},
            "resources": {"device": "cpu", "gpu_count": 0},
            "package_manifest": package_manifest(),
        }
        result = TrainingResult.model_validate({
            "protocol_version": "training-result/v1",
            "execution_id": execution_id,
            "status": "succeeded",
            "artifacts": [{"path": "model.pt", "role": "model", "format": "pt", "size_bytes": 5, "deployable": True}],
                    "model": {
                        "task_kind": "classification",
                        "class_names": ["cat", "dog"],
                        "framework": {"id": "pytorch", "version": "2.5"},
                    },
        })

        with self.assertRaises(TrainingRunnerError) as raised:
            _validate_output_contract(context, result)
        self.assertIn("format `pt`", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
