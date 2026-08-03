from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from contracts import TrainingResult
from runner import RESULT_PREFIX


RUNNER_PATH = Path(__file__).resolve().parents[1] / "runner.py"
SMOKE_PACKAGE_PATH = Path(__file__).resolve().parents[1] / "examples" / "pytorch-smoke-classifier" / "train.py"


class DeployableSmokeExampleTest(unittest.TestCase):
    def test_exports_deployable_onnx_with_model_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            output_dir = workspace / "output"
            context_path = workspace / "execution.json"
            context_path.write_text(
                json.dumps(
                    {
                        "execution_id": str(uuid4()),
                        "workspace": {"output_dir": str(output_dir)},
                        "dataset": {"class_names": ["negative", "positive"], "items": []},
                        "parameters": {"epochs": 1, "sample_count": 32},
                        "resources": {"device": "cpu"},
                    }
                ),
                encoding="utf-8",
            )
            process = subprocess.run(
                [sys.executable, str(RUNNER_PATH), str(SMOKE_PACKAGE_PATH), str(context_path)],
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(process.returncode, 0, process.stderr)
            result_line = next(
                line for line in process.stdout.splitlines() if line.startswith(RESULT_PREFIX)
            )
            result = TrainingResult.model_validate_json(
                (output_dir / "result.json").read_text(encoding="utf-8")
            )
            self.assertEqual(result.status, "succeeded")
            self.assertEqual(result.model.class_names, ["negative", "positive"])
            self.assertEqual(result.model.framework.id, "pytorch")
            self.assertEqual(result.artifacts[0].format, "onnx")
            self.assertTrue(result.artifacts[0].deployable)
            self.assertTrue((output_dir / "smoke-model.onnx").is_file())
            self.assertEqual(
                json.loads(result_line[len(RESULT_PREFIX) :])["artifacts"][0]["path"],
                "smoke-model.onnx",
            )
