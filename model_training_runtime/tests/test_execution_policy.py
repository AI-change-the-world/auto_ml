from __future__ import annotations

import unittest
from uuid import uuid4

from contracts import SUBMISSION_PROTOCOL_VERSION, TrainingCodeSubmission
from execution_policy import ExecutionPolicyError, validate_execution_policy


def submission(*, input_mode: str = "platform_dataset") -> TrainingCodeSubmission:
    payload = {
        "protocol_version": SUBMISSION_PROTOCOL_VERSION,
        "message_id": str(uuid4()),
        "execution_id": str(uuid4()),
        "task": {"task_id": 1, "task_kind": "classification"},
        "package": {
            "key": "policy-test-package",
            "version": "1.0.0",
            "sha256": "a" * 64,
        },
        "package_archive": {
            "bucket": "default",
            "object_key": "training-code-runtime/packages/policy-test-package/source.zip",
            "sha256": "a" * 64,
            "size_bytes": 1,
        },
        "runtime": {"id": "pytorch-2.5-cu124"},
        "resources": {"device": "cpu", "gpu_count": 0},
        "input_mode": input_mode,
    }
    if input_mode == "platform_dataset":
        payload["dataset_source_snapshot"] = {
            "bucket": "default",
            "object_key": "training-code-runtime/datasets/policy-test.json",
            "sha256": "b" * 64,
            "size_bytes": 1,
        }
    else:
        payload["script_dataset"] = {
            "protocol_version": "training-dataset-manifest/v1",
            "task_kind": "classification",
            "data_modalities": ["image"],
            "annotation_kinds": [],
            "class_names": ["cat", "dog"],
            "items": [],
        }
    return TrainingCodeSubmission.model_validate(payload)


class ExecutionPolicyTest(unittest.TestCase):
    def test_accepts_enabled_platform_dataset_execution(self) -> None:
        validate_execution_policy(
            submission(),
            {"enabled": True, "execution": {"enabled": True}},
        )

    def test_rejects_disabled_runtime_or_executor(self) -> None:
        with self.assertRaisesRegex(ExecutionPolicyError, "enabled is false"):
            validate_execution_policy(submission(), {"execution": {"enabled": True}})
        with self.assertRaisesRegex(ExecutionPolicyError, "execution.enabled is false"):
            validate_execution_policy(submission(), {"enabled": True})

    def test_requires_explicit_script_managed_data_policy(self) -> None:
        managed_submission = submission(input_mode="script_managed")
        with self.assertRaisesRegex(ExecutionPolicyError, "script-managed"):
            validate_execution_policy(
                managed_submission,
                {"enabled": True, "execution": {"enabled": True}},
            )
        validate_execution_policy(
            managed_submission,
            {
                "enabled": True,
                "allow_script_managed_data": True,
                "execution": {"enabled": True},
            },
        )

    def test_requires_an_enabled_platform_runtime(self) -> None:
        with self.assertRaisesRegex(ExecutionPolicyError, "not enabled"):
            validate_execution_policy(
                submission(),
                {
                    "enabled": True,
                    "execution": {
                        "enabled": True,
                        "runtime_ids": ["ultralytics-8.3.0-pytorch-2.5-cu124"],
                    },
                },
            )


if __name__ == "__main__":
    unittest.main()
