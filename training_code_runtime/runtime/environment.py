"""Platform-managed runtime selection; intentionally no venv or pip support."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable, Iterable

from .errors import RuntimeExecutionError
from .logging_utils import logger
from .models import ManagedRuntimeSpec, PreparedRuntime, RuntimeExecutionSettings


RUNTIME_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
EnvironmentOutputCallback = Callable[[str, str], None]


class ManagedRuntimeError(RuntimeExecutionError):
    pass


class PlatformRuntimeManager:
    """Resolves prebuilt, platform-controlled runtimes for a task workspace.

    A package selects only a registry key. The registry is created by service
    configuration or the worker image; this manager never accepts package
    dependencies, creates a venv, or invokes pip.
    """

    def __init__(
        self,
        settings: RuntimeExecutionSettings,
        runtimes: Iterable[ManagedRuntimeSpec],
        *,
        output_callback: EnvironmentOutputCallback | None = None,
    ) -> None:
        self.settings = settings
        self.runtimes = {runtime.runtime_id: runtime for runtime in runtimes}
        self.output_callback = output_callback

    def prepare(self, *, task_root: Path, runtime_id: str) -> PreparedRuntime:
        self._validate_task_root(task_root)
        runtime = self._resolve_runtime(runtime_id)
        python_executable = runtime.python_executable.resolve()
        if not python_executable.is_file():
            raise self._error(
                "resolve_runtime",
                "RuntimeUnavailable",
                f"platform runtime `{runtime_id}` has no executable at {python_executable}",
            )
        if not runtime.image_digest.startswith("sha256:") or len(runtime.image_digest) != 71:
            raise self._error(
                "resolve_runtime",
                "InvalidRuntimeDigest",
                f"platform runtime `{runtime_id}` has an invalid immutable image digest",
            )

        task_root = task_root.resolve()
        home_dir = task_root / "home"
        temp_dir = task_root / "tmp"
        for directory in (home_dir, temp_dir):
            directory.mkdir(parents=True, exist_ok=True)
        environment = self._build_environment(home_dir, temp_dir, python_executable)
        self._emit("resolve_runtime", f"Using platform-managed runtime `{runtime_id}`")
        logger.info(
            "Prepared managed training runtime: runtime_id=%s image=%s digest=%s task_root=%s",
            runtime.runtime_id,
            runtime.image_reference,
            runtime.image_digest,
            task_root,
        )
        return PreparedRuntime(
            runtime=runtime,
            task_root=task_root,
            home_dir=home_dir,
            temp_dir=temp_dir,
            environment=environment,
        )

    def _validate_task_root(self, task_root: Path) -> None:
        workspace_root = self.settings.workspace_root.resolve()
        resolved = task_root.resolve()
        try:
            resolved.relative_to(workspace_root)
        except ValueError as exc:
            raise self._error(
                "prepare_workspace",
                "WorkspaceEscape",
                f"task workspace must be below {workspace_root}",
            ) from exc

    def _resolve_runtime(self, runtime_id: str) -> ManagedRuntimeSpec:
        if not RUNTIME_ID_PATTERN.fullmatch(runtime_id):
            raise self._error("resolve_runtime", "InvalidRuntimeId", "runtime id has invalid characters")
        runtime = self.runtimes.get(runtime_id)
        if runtime is None:
            raise self._error(
                "resolve_runtime",
                "UnsupportedRuntime",
                f"platform runtime `{runtime_id}` is not registered",
            )
        return runtime

    @staticmethod
    def _build_environment(home_dir: Path, temp_dir: Path, python_executable: Path) -> dict[str, str]:
        environment = {
            **os.environ,
            "HOME": str(home_dir),
            "XDG_CACHE_HOME": str(home_dir / ".cache"),
            "XDG_CONFIG_HOME": str(home_dir / ".config"),
            "TMPDIR": str(temp_dir),
            "TMP": str(temp_dir),
            "TEMP": str(temp_dir),
            "PYTHONNOUSERSITE": "1",
            "PATH": f"{python_executable.parent}{os.pathsep}{os.environ.get('PATH', '')}",
        }
        for key in tuple(environment):
            if key == "VIRTUAL_ENV" or key.startswith("PIP_"):
                environment.pop(key, None)
        return environment

    def _emit(self, stage: str, message: str) -> None:
        if self.output_callback:
            self.output_callback(stage, message)

    @staticmethod
    def _error(stage: str, error_type: str, message: str) -> ManagedRuntimeError:
        return ManagedRuntimeError(
            message,
            {
                "source": "training_code_runtime",
                "stage": stage,
                "exception_type": error_type,
                "message": message,
            },
        )
