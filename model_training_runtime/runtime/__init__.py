"""Reusable foundation for the in-service model training worker."""
from .archive import TrainingArchiveError, extract_training_package, validate_archive_members
from .environment import ManagedRuntimeError, PlatformRuntimeManager, TrainingRuntimeManager
from .errors import RuntimeExecutionError
from .executor import (
    ExecutionLaunch,
    LocalSubprocessExecutor,
    ServiceSubprocessExecutor,
    TrainingExecutor,
    TrainingExecutorError,
)
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
    "ExecutionLaunch",
    "LocalSubprocessExecutor",
    "ServiceSubprocessExecutor",
    "LOG_PREFIX",
    "RESULT_PREFIX",
    "ManagedRuntimeError",
    "ManagedRuntimeSpec",
    "PlatformRuntimeManager",
    "TrainingRuntimeManager",
    "PreparedRuntime",
    "ProcessResult",
    "RunnerMessage",
    "RunnerProtocolError",
    "RuntimeExecutionError",
    "RuntimeExecutionSettings",
    "RuntimeProcessError",
    "TrainingArchiveError",
    "TrainingExecutor",
    "TrainingExecutorError",
    "build_resource_limit_command",
    "extract_training_package",
    "parse_runner_line",
    "run_isolated_process",
    "validate_archive_members",
]
