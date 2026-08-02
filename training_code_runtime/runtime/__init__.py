"""Reusable, non-business-specific foundation for training-code execution.

The modules are deliberately not connected to HTTP or MQ yet. They provide the
same execution primitives that the future training worker will need without
bringing batch-annotation behavior into this service.
"""
from .archive import TrainingArchiveError, extract_training_package, validate_archive_members
from .environment import ManagedRuntimeError, PlatformRuntimeManager
from .errors import RuntimeExecutionError
from .models import (
    ManagedRuntimeSpec,
    PreparedRuntime,
    ProcessResult,
    RunnerMessage,
    RuntimeExecutionSettings,
)
from .limits import build_resource_limit_command
from .parsing import RunnerProtocolError, parse_runner_line
from .process import RuntimeProcessError, run_isolated_process
from .protocol import EVENT_PREFIX, LOG_PREFIX, RESULT_PREFIX

__all__ = [
    "EVENT_PREFIX",
    "LOG_PREFIX",
    "RESULT_PREFIX",
    "ManagedRuntimeError",
    "ManagedRuntimeSpec",
    "PlatformRuntimeManager",
    "PreparedRuntime",
    "ProcessResult",
    "RunnerMessage",
    "RunnerProtocolError",
    "RuntimeExecutionError",
    "RuntimeExecutionSettings",
    "RuntimeProcessError",
    "TrainingArchiveError",
    "build_resource_limit_command",
    "extract_training_package",
    "parse_runner_line",
    "run_isolated_process",
    "validate_archive_members",
]
