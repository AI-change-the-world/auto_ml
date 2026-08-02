from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from uuid import uuid4

from contracts import EVENT_PROTOCOL_VERSION, RESULT_PROTOCOL_VERSION
from runtime import (
    EVENT_PREFIX,
    RESULT_PREFIX,
    ManagedRuntimeError,
    ManagedRuntimeSpec,
    PlatformRuntimeManager,
    RunnerProtocolError,
    RuntimeExecutionSettings,
    RuntimeProcessError,
    TrainingArchiveError,
    build_resource_limit_command,
    extract_training_package,
    parse_runner_line,
    run_isolated_process,
)


def managed_runtime() -> ManagedRuntimeSpec:
    return ManagedRuntimeSpec(
        runtime_id="python-test-runtime",
        python_executable=Path(sys.executable),
    )


class TrainingRuntimeFoundationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_extracts_package_and_rejects_dynamic_dependencies(self) -> None:
        archive_path = self.root / "package.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("training_package.json", "{}")
            archive.writestr("train.py", "def train(context, report): return {}\n")

        files, total_size = extract_training_package(archive_path, self.root / "code")
        self.assertIn("train.py", files)
        self.assertGreater(total_size, 0)
        self.assertTrue((self.root / "code" / "train.py").is_file())

        forbidden_archive = self.root / "forbidden.zip"
        with zipfile.ZipFile(forbidden_archive, "w") as archive:
            archive.writestr("training_package.json", "{}")
            archive.writestr("train.py", "pass\n")
            archive.writestr("requirements.txt", "torch\n")
        with self.assertRaises(TrainingArchiveError):
            extract_training_package(forbidden_archive, self.root / "forbidden")

    def test_prepares_registered_runtime_without_venv_or_pip_environment(self) -> None:
        workspace_root = self.root / "workspaces"
        task_root = workspace_root / "task-1"
        settings = RuntimeExecutionSettings(workspace_root=workspace_root)
        manager = PlatformRuntimeManager(settings, [managed_runtime()])

        prepared = manager.prepare(task_root=task_root, runtime_id="python-test-runtime")
        self.assertEqual(prepared.runtime.runtime_id, "python-test-runtime")
        self.assertTrue(prepared.home_dir.is_dir())
        self.assertTrue(prepared.temp_dir.is_dir())
        self.assertNotIn("VIRTUAL_ENV", prepared.environment)
        self.assertFalse(any(key.startswith("PIP_") for key in prepared.environment))

        with self.assertRaises(ManagedRuntimeError) as raised:
            manager.prepare(task_root=task_root, runtime_id="not-registered")
        self.assertEqual(raised.exception.error_detail["exception_type"], "UnsupportedRuntime")

    def test_rejects_workspace_escape(self) -> None:
        settings = RuntimeExecutionSettings(workspace_root=self.root / "workspaces")
        manager = PlatformRuntimeManager(settings, [managed_runtime()])
        with self.assertRaises(ManagedRuntimeError) as raised:
            manager.prepare(task_root=self.root / "outside", runtime_id="python-test-runtime")
        self.assertEqual(raised.exception.error_detail["exception_type"], "WorkspaceEscape")

    def test_process_streams_lines_and_enforces_output_limit(self) -> None:
        received: list[tuple[str, str]] = []
        result = run_isolated_process(
            [sys.executable, "-c", "print('first'); print('second')"],
            cwd=self.root,
            env={**os.environ, "PATH": os.environ.get("PATH", "")},
            stage="line_test",
            timeout_seconds=10,
            idle_timeout_seconds=2,
            max_output_bytes=1024,
            line_callback=lambda stream, line: received.append((stream, line)),
        )
        self.assertEqual(result.return_code, 0)
        self.assertEqual(received, [("stdout", "first"), ("stdout", "second")])

        with self.assertRaises(RuntimeProcessError) as raised:
            run_isolated_process(
                [sys.executable, "-c", "print('x' * 2048)"],
                cwd=self.root,
                env={**os.environ, "PATH": os.environ.get("PATH", "")},
                stage="output_limit_test",
                timeout_seconds=10,
                idle_timeout_seconds=2,
                max_output_bytes=128,
            )
        self.assertEqual(raised.exception.error_detail["exception_type"], "OutputLimitExceeded")

    def test_parses_runner_event_and_result_lines(self) -> None:
        execution_id = str(uuid4())
        event_line = EVENT_PREFIX + json.dumps({
            "protocol_version": EVENT_PROTOCOL_VERSION,
            "execution_id": execution_id,
            "sequence": 0,
            "occurred_at": "2026-08-02T00:00:00Z",
            "event_type": "phase",
            "phase": "prepare",
        })
        event = parse_runner_line(event_line)
        self.assertEqual(event.channel, "event")

        result_line = RESULT_PREFIX + json.dumps({
            "protocol_version": RESULT_PROTOCOL_VERSION,
            "execution_id": execution_id,
            "status": "failed",
            "error": {"stage": "train", "error_type": "RuntimeError", "message": "expected"},
        })
        result = parse_runner_line(result_line)
        self.assertEqual(result.channel, "result")
        self.assertEqual(result.payload["status"], "failed")

        with self.assertRaises(RunnerProtocolError):
            parse_runner_line(EVENT_PREFIX + "not-json")

    def test_builds_optional_linux_process_limit_command(self) -> None:
        settings = RuntimeExecutionSettings(workspace_root=self.root, max_processes=12)
        command = build_resource_limit_command(settings, memory_bytes=1024 * 1024, cpu_seconds=30)
        if os.name == "posix" and shutil.which("prlimit"):
            self.assertIsNotNone(command)
            self.assertIn("--nproc=12", command)
            self.assertIn("--cpu=30", command)
        else:
            self.assertIsNone(command)


if __name__ == "__main__":
    unittest.main()
