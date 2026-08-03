from __future__ import annotations

import unittest

from core.deploy_service import DeployService
from core.runtime_manager import RuntimeInstance


class RuntimeCacheAndClassificationTest(unittest.TestCase):
    def test_cache_path_changes_when_immutable_object_key_changes(self) -> None:
        service = DeployService()
        first = service._local_model_path(1, "training/executions/a/model.onnx", "onnx")
        second = service._local_model_path(1, "training/executions/b/model.onnx", "onnx")

        self.assertNotEqual(first, second)
        self.assertTrue(first.endswith(".onnx"))
        self.assertIn("model_1_", first)

    def test_rejects_detection_output_for_classification_runtime(self) -> None:
        instance = RuntimeInstance(
            model_id=1,
            model_path="model.onnx",
            task_kind="classification",
            class_names=["negative", "positive"],
        )
        with self.assertRaisesRegex(RuntimeError, "Classification deployment requires"):
            instance._validate_classification_output_signature([1, 6, 8400])

    def test_rejects_mismatched_classification_class_count(self) -> None:
        instance = RuntimeInstance(
            model_id=1,
            model_path="model.onnx",
            task_kind="classification",
            class_names=["negative", "positive"],
        )
        with self.assertRaisesRegex(RuntimeError, "class count does not match"):
            instance._validate_classification_output_signature([1, 1000])
