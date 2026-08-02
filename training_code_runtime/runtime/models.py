"""Runtime value objects independent of MQ, storage, and HTTP."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


@dataclass(frozen=True)
class ProcessResult:
    return_code: int
    stdout: str
    stderr: str
    stdout_bytes: int
    stderr_bytes: int


@dataclass(frozen=True)
class ManagedRuntimeSpec:
    """A platform-owned immutable runtime, never supplied by package code."""

    runtime_id: str
    image_reference: str
    image_digest: str
    python_executable: Path


@dataclass(frozen=True)
class RuntimeExecutionSettings:
    """Process and workspace constraints applied by the later execution worker."""

    workspace_root: Path
    idle_timeout_seconds: int = 180
    max_output_bytes: int = 2 * 1024 * 1024
    max_processes: int = 32
    process_fsize_bytes: int = 50 * 1024 * 1024
    process_nofile: int = 512


@dataclass(frozen=True)
class PreparedRuntime:
    runtime: ManagedRuntimeSpec
    task_root: Path
    home_dir: Path
    temp_dir: Path
    environment: dict[str, str]


@dataclass(frozen=True)
class RunnerMessage:
    channel: Literal["event", "log", "result"]
    payload: dict[str, Any]
