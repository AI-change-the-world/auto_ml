from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from contracts import TrainingResult
from runner import EVENT_PREFIX, LOG_PREFIX, RESULT_PREFIX


RUNNER_PATH = Path(__file__).resolve().parents[1] / "runner.py"


def execution_context(output_dir: Path) -> dict:
    return {
        "execution_id": str(uuid4()),
        "task": {"task_id": 1, "task_kind": "classification"},
        "workspace": {"output_dir": str(output_dir)},
        "dataset": {"class_names": ["cat", "dog"], "items": []},
        "parameters": {"epochs": 2},
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


if __name__ == "__main__":
    unittest.main()
