"""Runtime value objects shared by the batch worker."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessResult:
    return_code: int
    stdout: str
    stderr: str
    stdout_bytes: int
    stderr_bytes: int


@dataclass(frozen=True)
class ScriptEnvironment:
    python_executable: Path
    venv_dir: Path
    packages: list[str]
    requirements_file: Path | None
    elapsed_seconds: float
