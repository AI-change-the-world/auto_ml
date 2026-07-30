from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid
import zipfile
from pathlib import Path

from config import ScriptRuntimeSettings
from runtime.archive import extract_script_package
from runtime.environment import ScriptEnvironmentManager
from runtime.parsing import load_package_environment
from runtime.process import RuntimeProcessError, run_isolated_process


def _test_workspace_root() -> Path:
    configured_root = os.getenv("PIPELINE_SANDBOX_TEST_WORKSPACE")
    if configured_root:
        return Path(configured_root)
    runtime_root = Path("/app/runtime-data")
    if runtime_root.is_dir():
        return runtime_root / "tests"
    return Path(__file__).resolve().parents[1] / ".runtime-test-workspace"


class BatchRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = _test_workspace_root() / uuid.uuid4().hex
        self.root.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        try:
            self.root.parent.rmdir()
        except OSError:
            pass

    def test_extracts_zip_and_loads_package_environment(self) -> None:
        archive_path = self.root / "script.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("main.py", "def execute_batch(params):\n    return {'items': []}\n")
            archive.writestr(".env", "MODEL_REGION=cn-hangzhou\nQUOTED=\"value\"\n")

        package_root = self.root / "script"
        extract_script_package(archive_path, package_root)

        self.assertTrue((package_root / "main.py").is_file())
        self.assertEqual(
            load_package_environment(package_root),
            {"MODEL_REGION": "cn-hangzhou", "QUOTED": "value"},
        )

    def test_installs_local_requirement_into_cached_venv(self) -> None:
        script_root = self.root / "script"
        package_root = script_root / "packages"
        wheel_path = package_root / "runtime_fixture-0.0.1-py3-none-any.whl"
        package_root.mkdir(parents=True)
        _write_local_wheel(wheel_path)
        requirements_file = script_root / "requirements.txt"
        requirements_file.write_text(f"{wheel_path.relative_to(script_root)}\n", encoding="utf-8")

        settings = ScriptRuntimeSettings(
            venv_root=self.root / "venvs",
            pip_cache_dir=self.root / "pip-cache",
            pip_index_url=None,
            pip_extra_index_url=None,
            pip_trusted_host=None,
            idle_timeout_seconds=30,
            bootstrap_max_processes=128,
            process_fsize_bytes=50 * 1024 * 1024,
            process_nofile=256,
        )
        manager = ScriptEnvironmentManager(settings, timeout_seconds=60, max_output_bytes=1024 * 1024)

        environment = manager.prepare(
            task_root=self.root,
            script_key="runtime-fixture",
            script_version="1.0.0",
            requirements_file=requirements_file,
        )
        result = subprocess.run(
            [str(environment.python_executable), "-c", "import runtime_fixture; print(runtime_fixture.VALUE)"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        reused_environment = manager.prepare(
            task_root=self.root,
            script_key="runtime-fixture",
            script_version="1.0.0",
            requirements_file=requirements_file,
        )

        self.assertEqual(result.stdout.strip(), "installed-from-requirements")
        self.assertEqual(environment.venv_dir, reused_environment.venv_dir)
        self.assertTrue((environment.venv_dir / ".batch-sandbox-environment.json").is_file())

    @unittest.skipUnless(shutil.which("prlimit"), "prlimit is required for Linux resource-limit coverage")
    def test_bootstraps_pip_with_prlimit_process_limit(self) -> None:
        settings = ScriptRuntimeSettings(
            venv_root=self.root / "venvs",
            pip_cache_dir=self.root / "pip-cache",
            pip_index_url=None,
            pip_extra_index_url=None,
            pip_trusted_host=None,
            idle_timeout_seconds=30,
            bootstrap_max_processes=128,
            process_fsize_bytes=50 * 1024 * 1024,
            process_nofile=256,
        )
        manager = ScriptEnvironmentManager(
            settings,
            timeout_seconds=60,
            max_output_bytes=1024 * 1024,
            resource_limit_command=[str(shutil.which("prlimit")), "--nproc=128", "--"],
        )

        environment = manager.prepare(
            task_root=self.root,
            script_key="limited-bootstrap",
            script_version="1.0.0",
            requirements_file=None,
        )

        self.assertTrue(environment.python_executable.is_file())
        self.assertTrue((environment.venv_dir / ".batch-sandbox-environment.json").is_file())

    def test_stops_process_group_after_idle_timeout(self) -> None:
        marker_path = self.root / "child-completed"
        child_code = f"import time; time.sleep(2); open({str(marker_path)!r}, 'w').write('unexpected')"
        code = f"import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {child_code!r}]); time.sleep(5)"

        with self.assertRaises(RuntimeProcessError) as raised:
            run_isolated_process(
                [sys.executable, "-c", code],
                cwd=self.root,
                env={**os.environ, "PATH": os.environ.get("PATH", "")},
                stage="idle_timeout_test",
                timeout_seconds=10,
                idle_timeout_seconds=1,
                max_output_bytes=1024,
                resource_limit_command=None,
            )

        self.assertEqual(raised.exception.error_detail["exception_type"], "IdleTimeoutError")
        self.assertFalse(marker_path.exists())

    def test_stops_script_when_output_limit_is_exceeded(self) -> None:
        with self.assertRaises(RuntimeProcessError) as raised:
            run_isolated_process(
                [sys.executable, "-c", "print('x' * 2048)"],
                cwd=self.root,
                env={**os.environ, "PATH": os.environ.get("PATH", "")},
                stage="output_limit_test",
                timeout_seconds=10,
                idle_timeout_seconds=2,
                max_output_bytes=128,
                resource_limit_command=None,
            )

        self.assertEqual(raised.exception.error_detail["exception_type"], "OutputLimitExceeded")

    def test_uploaded_zip_example_runs_through_runner_contract(self) -> None:
        example_root = Path(__file__).resolve().parents[2] / "readme" / "batch-script-zip-example"
        example_zip = self.root / "image_center_box_zip_check.zip"
        with zipfile.ZipFile(example_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in ("batch_script.json", "requirements.txt", "image_center_box.py", "box_utils.py"):
                archive.write(example_root / name, name)
        package_root = self.root / "uploaded-script"
        extract_script_package(example_zip, package_root)
        image_path = self.root / "sample.png"
        image_path.write_bytes(
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADElEQVR42mNk+M/wHwAF/gL+Q10r7QAAAABJRU5ErkJggg=="
            )
        )
        payload_path = self.root / "payload.json"
        payload_path.write_text(
            json.dumps(
                {
                    "script_params": {"class_index": 0, "box_width": 0.5, "box_height": 0.5},
                    "items": [{"batch_item_id": 42, "local_path": str(image_path)}],
                }
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve().parents[1] / "runner.py"),
                str(package_root / "image_center_box.py"),
                str(payload_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        lines = result.stdout.splitlines()
        progress_event = json.loads(next(line.split("=", 1)[1] for line in lines if line.startswith("__AUTO_ML_BATCH_EVENT__=")))
        response = json.loads(next(line.split("=", 1)[1] for line in lines if line.startswith("__AUTO_ML_BATCH_RESULT__=")))
        item = response["data"]["items"][0]
        self.assertEqual(progress_event["batch_item_id"], 42)
        self.assertEqual(item["status"], "succeeded")
        self.assertEqual(item["content"]["label_text"], "0 0.500000 0.500000 0.500000 0.500000")
        self.assertEqual(item["content"]["image_width"], 1)
        self.assertEqual(item["content"]["image_height"], 1)


def _write_local_wheel(path: Path) -> None:
    module_content = "VALUE = 'installed-from-requirements'\n"
    metadata = "Metadata-Version: 2.1\nName: runtime-fixture\nVersion: 0.0.1\n"
    wheel = "Wheel-Version: 1.0\nGenerator: auto-ml-runtime-test\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    files = {
        "runtime_fixture.py": module_content.encode("utf-8"),
        "runtime_fixture-0.0.1.dist-info/METADATA": metadata.encode("utf-8"),
        "runtime_fixture-0.0.1.dist-info/WHEEL": wheel.encode("utf-8"),
    }
    records = []
    for name, content in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode("ascii")
        records.append(f"{name},sha256={digest},{len(content)}")
    records.append("runtime_fixture-0.0.1.dist-info/RECORD,,")
    files["runtime_fixture-0.0.1.dist-info/RECORD"] = ("\n".join(records) + "\n").encode("utf-8")

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)


if __name__ == "__main__":
    unittest.main()
