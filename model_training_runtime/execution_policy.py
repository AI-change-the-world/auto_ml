"""Platform policy checks shared by HTTP and MQ execution paths."""
from __future__ import annotations

from typing import Any

from contracts import TrainingCodeSubmission, TrainingDataInputMode


DEFAULT_RUNTIME_IDS = {
    "ultralytics-8.3.0-pytorch-2.5-cu124",
    "pytorch-2.5-cu124",
}


class ExecutionPolicyError(RuntimeError):
    """A structurally valid submission is disabled by platform policy."""


def validate_execution_policy(
    submission: TrainingCodeSubmission,
    config: dict[str, Any],
) -> None:
    """Reject submissions that bypass the control-plane execution switches."""
    if config.get("enabled") is not True:
        raise ExecutionPolicyError("model-training-runtime.enabled is false")

    execution = config.get("execution")
    if not isinstance(execution, dict) or execution.get("enabled") is not True:
        raise ExecutionPolicyError("model-training-runtime.execution.enabled is false")

    runtime_ids = execution.get("runtime_ids", DEFAULT_RUNTIME_IDS)
    if isinstance(runtime_ids, str):
        runtime_ids = [runtime_ids]
    if (
        not isinstance(runtime_ids, (list, set, tuple))
        or not all(isinstance(runtime_id, str) and runtime_id.strip() for runtime_id in runtime_ids)
    ):
        raise ExecutionPolicyError("model-training-runtime.execution.runtime_ids is invalid")
    if submission.runtime.id not in runtime_ids:
        raise ExecutionPolicyError(
            f"training runtime `{submission.runtime.id}` is not enabled for execution"
        )

    if (
        submission.input_mode == TrainingDataInputMode.SCRIPT_MANAGED
        and config.get("allow_script_managed_data") is not True
    ):
        raise ExecutionPolicyError("script-managed training data is disabled by platform policy")
