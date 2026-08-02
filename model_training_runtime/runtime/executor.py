"""Execution backends for prepared training workspaces.

An executor receives only workspace-local inputs prepared by the coordinator.
It starts the runner in the service subprocess today and streams its lines
back. It does not resolve S3 objects, interpret package output, or persist
lifecycle state.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from contracts import TrainingExecutionRequest

from .limits import build_resource_limit_command
from .errors import RuntimeExecutionError
from .models import PreparedRuntime, ProcessResult, RuntimeExecutionSettings
from .process import run_isolated_process


LineCallback = Callable[[str, str], None]


class TrainingExecutorError(RuntimeExecutionError):
    """An execution backend could not launch the prepared runner."""


@dataclass(frozen=True)
class ExecutionLaunch:
    """A fully prepared task workspace ready for an executor to start.

    ``execution`` retains portable ``/workspace`` contract paths.  The local
    executor maps those paths to the private host workspace; a container or Job
    executor should mount the workspace at ``/workspace`` and pass it through
    unchanged.
    """

    execution: TrainingExecutionRequest
    task_root: Path
    code_dir: Path
    input_dir: Path
    output_dir: Path
    entrypoint_path: Path
    prepared_runtime: PreparedRuntime
    runtime_settings: RuntimeExecutionSettings
    model_input_path: Path | None = None


class TrainingExecutor(Protocol):
    """Starts one prepared runner without owning its result semantics."""

    supported_devices: frozenset[str]

    async def execute(
        self,
        launch: ExecutionLaunch,
        *,
        line_callback: LineCallback | None = None,
    ) -> ProcessResult: ...


class LocalSubprocessExecutor:
    """Test-only executor that starts the runner in a host subprocess.

    This is not a sandbox.  It exists solely to exercise the coordinator before
    a container or Job implementation owns resource and security isolation.
    """

    supported_devices = frozenset({"cpu"})

    def __init__(self, *, runner_path: Path | None = None) -> None:
        self.runner_path = (runner_path or Path(__file__).parents[1] / "runner.py").resolve()

    async def execute(
        self,
        launch: ExecutionLaunch,
        *,
        line_callback: LineCallback | None = None,
    ) -> ProcessResult:
        if not self.runner_path.is_file():
            message = f"platform runner is unavailable at {self.runner_path}"
            raise TrainingExecutorError(
                message,
                {
                    "source": "model_training_runtime",
                    "stage": "launch_runner",
                    "exception_type": "RunnerUnavailable",
                    "message": message,
                },
            )
        context_path = launch.task_root / "execution.local.json"
        context_path.write_text(
            json.dumps(self._local_runner_context(launch), ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        runtime = launch.prepared_runtime.runtime
        return run_isolated_process(
            [
                str(runtime.python_executable),
                str(self.runner_path),
                str(launch.entrypoint_path),
                str(context_path),
            ],
            cwd=launch.code_dir,
            env=launch.prepared_runtime.environment,
            stage="run_training_code",
            timeout_seconds=launch.execution.resources.timeout_seconds,
            idle_timeout_seconds=launch.runtime_settings.idle_timeout_seconds,
            max_output_bytes=launch.runtime_settings.max_output_bytes,
            resource_limit_command=build_resource_limit_command(
                launch.runtime_settings,
                memory_bytes=launch.execution.resources.memory_bytes,
                cpu_seconds=launch.execution.resources.timeout_seconds,
            ),
            line_callback=line_callback,
        )

    @staticmethod
    def _local_runner_context(launch: ExecutionLaunch) -> dict[str, Any]:
        context = launch.execution.model_dump(mode="json", exclude={"package_manifest"})
        context["workspace"] = {
            "root_dir": str(launch.task_root),
            "code_dir": str(launch.code_dir),
            "input_dir": str(launch.input_dir),
            "output_dir": str(launch.output_dir),
            "dataset_manifest_path": str(launch.input_dir / "dataset-manifest.json"),
        }
        if launch.model_input_path is not None:
            context["model_input_path"] = str(launch.model_input_path)
        return context


class ServiceSubprocessExecutor(LocalSubprocessExecutor):
    """In-service executor used by the first real training worker.

    The worker process owns the platform runtime and resource policy. GPU
    visibility is supplied by the service deployment; a later scheduler can
    add per-task ``CUDA_VISIBLE_DEVICES`` allocation without changing the
    runner protocol.
    """

    supported_devices = frozenset({"cpu", "cuda"})
