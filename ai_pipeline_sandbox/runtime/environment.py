"""Virtual environment creation, package installation, and dependency caching."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

from .config import ScriptRuntimeSettings

from .errors import RuntimeExecutionError
from .logging_utils import logger
from .models import ScriptEnvironment
from .process import RuntimeProcessError, run_isolated_process


ENVIRONMENT_MARKER = ".batch-sandbox-environment.json"
BUILTIN_SCRIPT_PACKAGES: dict[str, list[str]] = {
    "vision_llm_bbox_assistant": ["openai==1.109.1"],
}
_environment_locks: dict[str, threading.Lock] = {}
_environment_locks_guard = threading.Lock()
EnvironmentOutputCallback = Callable[[str, str], None]


class ScriptEnvironmentError(RuntimeExecutionError):
    pass


class ScriptEnvironmentManager:
    def __init__(
        self,
        settings: ScriptRuntimeSettings,
        timeout_seconds: int,
        max_output_bytes: int,
        *,
        resource_limit_command: list[str] | None = None,
        output_callback: EnvironmentOutputCallback | None = None,
    ) -> None:
        self.settings = settings
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes
        self.resource_limit_command = resource_limit_command
        self.output_callback = output_callback

    def prepare(
        self,
        *,
        task_root: Path,
        script_key: str,
        script_version: str,
        requirements_file: Path | None,
    ) -> ScriptEnvironment:
        started_at = time.monotonic()
        deadline = started_at + self.timeout_seconds
        packages = list(BUILTIN_SCRIPT_PACKAGES.get(script_key, []))
        requirements_content = self._read_requirements(requirements_file)
        marker = self._build_marker(
            script_key=script_key,
            script_version=script_version,
            packages=packages,
            requirements_content=requirements_content,
        )
        venv_dir = self.settings.venv_root / self._environment_name(script_key, marker)
        python_executable = self._venv_python(venv_dir)
        logger.info(
            "Preparing script environment: script_key={} version={} venv_dir={} requirements_present={} builtin_package_count={}",
            script_key,
            script_version,
            venv_dir,
            requirements_file is not None,
            len(packages),
        )
        lock = self._lock_for(venv_dir)
        with lock:
            if self._marker_matches(venv_dir, marker) and python_executable.is_file():
                self._emit("reuse_venv", f"Reusing cached virtual environment: {venv_dir}")
                logger.info("Reusing cached script environment: script_key={} venv_dir={}", script_key, venv_dir)
                return ScriptEnvironment(
                    python_executable,
                    venv_dir,
                    packages,
                    requirements_file,
                    time.monotonic() - started_at,
                )

            if venv_dir.exists():
                logger.warning("Removing incomplete or stale batch script venv: {}", venv_dir)
                shutil.rmtree(venv_dir, ignore_errors=True)
            venv_dir.parent.mkdir(parents=True, exist_ok=True)
            self.settings.pip_cache_dir.mkdir(parents=True, exist_ok=True)
            self._create_venv(task_root, script_key, venv_dir, deadline)
            self._install_dependencies(
                task_root=task_root,
                script_key=script_key,
                python_executable=python_executable,
                packages=packages,
                requirements_file=requirements_file,
                venv_dir=venv_dir,
                deadline=deadline,
            )
            (venv_dir / ENVIRONMENT_MARKER).write_text(
                json.dumps(marker, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        logger.info(
            "Script environment prepared: script_key={} venv_dir={} elapsed_seconds={:.2f}",
            script_key,
            venv_dir,
            time.monotonic() - started_at,
        )
        return ScriptEnvironment(
            python_executable,
            venv_dir,
            packages,
            requirements_file,
            time.monotonic() - started_at,
        )

    def _create_venv(self, task_root: Path, script_key: str, venv_dir: Path, deadline: float) -> None:
        self._emit("create_venv", f"Creating virtual environment: {venv_dir}")
        self._run_command(
            [sys.executable, "-m", "venv", "--without-pip", str(venv_dir)],
            task_root,
            script_key,
            "create_venv",
            venv_dir,
            deadline,
            include_package_index=True,
        )
        self._emit("bootstrap_pip", "Bootstrapping pip with ensurepip")
        self._run_command(
            [str(self._venv_python(venv_dir)), "-m", "ensurepip", "--upgrade"],
            task_root,
            script_key,
            "bootstrap_pip",
            venv_dir,
            deadline,
            include_package_index=False,
        )

    def _install_dependencies(
        self,
        *,
        task_root: Path,
        script_key: str,
        python_executable: Path,
        packages: list[str],
        requirements_file: Path | None,
        venv_dir: Path,
        deadline: float,
    ) -> None:
        if not packages and requirements_file is None:
            self._emit("install_dependencies", "No additional Python dependencies requested")
            return
        requested = [*packages]
        if requirements_file is not None:
            requested.append(f"-r {requirements_file.name}")
        self._emit("install_dependencies", f"Installing Python dependencies: {', '.join(requested)}")
        command = [
            str(python_executable),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            *packages,
        ]
        if requirements_file is not None:
            command.extend(["-r", str(requirements_file)])
        self._run_command(
            command,
            task_root,
            script_key,
            "install_dependencies",
            venv_dir,
            deadline,
            include_package_index=True,
            working_directory=requirements_file.parent if requirements_file is not None else task_root,
        )

    def _run_command(
        self,
        command: list[str],
        task_root: Path,
        script_key: str,
        stage: str,
        venv_dir: Path,
        deadline: float,
        *,
        include_package_index: bool,
        working_directory: Path | None = None,
    ) -> None:
        remaining_seconds = deadline - time.monotonic()
        try:
            result = run_isolated_process(
                command,
                cwd=working_directory or task_root,
                env=self._build_environment(task_root, venv_dir, include_package_index=include_package_index),
                stage=stage,
                timeout_seconds=remaining_seconds,
                idle_timeout_seconds=self.settings.idle_timeout_seconds,
                max_output_bytes=self.max_output_bytes,
                resource_limit_command=self.resource_limit_command,
                line_callback=lambda stream, line: self._emit_output(script_key, stage, stream, line),
            )
        except RuntimeProcessError as exc:
            logger.error(
                "Batch script environment step failed: script_key={} stage={} detail={}",
                script_key,
                stage,
                exc.error_detail,
            )
            raise ScriptEnvironmentError(str(exc), dict(exc.error_detail)) from exc

        if result.return_code == 0:
            logger.info(
                "Batch script environment step completed: script_key={} stage={} stdout_bytes={} stderr_bytes={}",
                script_key,
                stage,
                result.stdout_bytes,
                result.stderr_bytes,
            )
            return
        output_tail = _combined_output_tail(result.stdout, result.stderr)
        logger.error(
            "Batch script environment step failed: script_key={} stage={} exit_code={}\n{}",
            script_key,
            stage,
            result.return_code,
            output_tail,
        )
        raise ScriptEnvironmentError(
            f"{stage} failed with exit code {result.return_code}",
            {
                "source": "sandbox",
                "stage": stage,
                "exception_type": "SubprocessError",
                "exit_code": result.return_code,
                "message": f"{stage} failed with exit code {result.return_code}",
                "output_tail": output_tail,
                "stdout_bytes": result.stdout_bytes,
                "stderr_bytes": result.stderr_bytes,
            },
        )

    def _emit_output(self, script_key: str, stage: str, stream: str, line: str) -> None:
        if line:
            logger.info(
                "Batch script environment output: script_key={} stage={} stream={} line={}",
                script_key,
                stage,
                stream,
                line,
            )
        if self.output_callback and line:
            self.output_callback(stage, line)

    def _emit(self, stage: str, message: str) -> None:
        logger.info("Batch script environment: stage={} message={}", stage, message)
        if self.output_callback:
            self.output_callback(stage, message)

    def _build_marker(
        self,
        *,
        script_key: str,
        script_version: str,
        packages: list[str],
        requirements_content: str,
    ) -> dict[str, Any]:
        return {
            "version": 1,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            "script_key": script_key,
            "script_version": script_version,
            "packages": sorted(packages),
            "requirements_sha256": hashlib.sha256(requirements_content.encode("utf-8")).hexdigest(),
            "pip_index_url": self.settings.pip_index_url,
            "pip_extra_index_url": self.settings.pip_extra_index_url,
            "pip_trusted_host": self.settings.pip_trusted_host,
        }

    @staticmethod
    def _read_requirements(requirements_file: Path | None) -> str:
        if requirements_file is None:
            return ""
        if not requirements_file.is_file():
            raise ScriptEnvironmentError(
                "script requirements file is unavailable",
                {
                    "source": "sandbox",
                    "stage": "load_requirements",
                    "message": "script requirements file is unavailable",
                },
            )
        if requirements_file.stat().st_size > 256 * 1024:
            raise ScriptEnvironmentError(
                "script requirements.txt exceeds the 256 KB limit",
                {
                    "source": "sandbox",
                    "stage": "load_requirements",
                    "message": "script requirements.txt exceeds the 256 KB limit",
                },
            )
        try:
            return requirements_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ScriptEnvironmentError(
                "script requirements.txt must be UTF-8",
                {
                    "source": "sandbox",
                    "stage": "load_requirements",
                    "message": "script requirements.txt must be UTF-8",
                },
            ) from exc

    @staticmethod
    def _venv_python(venv_dir: Path) -> Path:
        return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    @staticmethod
    def _environment_name(script_key: str, marker: dict[str, Any]) -> str:
        normalized_key = re.sub(r"[^a-zA-Z0-9_.-]+", "_", script_key).strip("._") or "script"
        digest = hashlib.sha256(json.dumps(marker, sort_keys=True).encode("utf-8")).hexdigest()[:20]
        return f"{normalized_key}_{digest}"

    @staticmethod
    def _marker_matches(venv_dir: Path, expected: dict[str, Any]) -> bool:
        try:
            marker = json.loads((venv_dir / ENVIRONMENT_MARKER).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return marker == expected

    @staticmethod
    def _lock_for(venv_dir: Path) -> threading.Lock:
        key = str(venv_dir)
        with _environment_locks_guard:
            lock = _environment_locks.get(key)
            if lock is None:
                lock = threading.Lock()
                _environment_locks[key] = lock
            return lock

    def _build_environment(
        self,
        task_root: Path,
        venv_dir: Path,
        *,
        include_package_index: bool,
    ) -> dict[str, str]:
        task_home = task_root / "home"
        task_tmp = task_root / "tmp"
        task_home.mkdir(parents=True, exist_ok=True)
        task_tmp.mkdir(parents=True, exist_ok=True)
        environment = {
            **os.environ,
            "HOME": str(task_home),
            "XDG_CACHE_HOME": str(task_home / ".cache"),
            "XDG_CONFIG_HOME": str(task_home / ".config"),
            "TMPDIR": str(task_tmp),
            "TMP": str(task_tmp),
            "TEMP": str(task_tmp),
            "PIP_CACHE_DIR": str(self.settings.pip_cache_dir),
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INPUT": "1",
            "VIRTUAL_ENV": str(venv_dir),
        }
        if include_package_index and self.settings.pip_index_url:
            environment["PIP_INDEX_URL"] = self.settings.pip_index_url
        else:
            environment.pop("PIP_INDEX_URL", None)
        if include_package_index and self.settings.pip_extra_index_url:
            environment["PIP_EXTRA_INDEX_URL"] = self.settings.pip_extra_index_url
        else:
            environment.pop("PIP_EXTRA_INDEX_URL", None)
        if include_package_index and self.settings.pip_trusted_host:
            environment["PIP_TRUSTED_HOST"] = self.settings.pip_trusted_host
        else:
            environment.pop("PIP_TRUSTED_HOST", None)
        return environment


def _combined_output_tail(stdout: str, stderr: str) -> str:
    stdout_tail = stdout[-8 * 1024 :]
    stderr_tail = stderr[-8 * 1024 :]
    if stdout_tail and stderr_tail:
        return f"stdout:\n{stdout_tail}\nstderr:\n{stderr_tail}"
    return stdout_tail or stderr_tail
