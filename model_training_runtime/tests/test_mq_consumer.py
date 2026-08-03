from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mq_consumer import TrainingCodeConsumer, _runtime_template


class TrainingCodeConsumerSettingsTest(unittest.TestCase):
    def test_uses_shared_platform_rabbitmq_configuration(self) -> None:
        platform_config = {
            "rabbitmq": {
                "host": "127.0.0.1",
                "port": 5672,
                "username": "automl",
                "password": "automl123456",
                "virtual_host": "/",
                "exchange_name": "auto_ml_exchange",
                "exchange_type": "topic",
                "queues": {"training_code_execute": "training.code.execute"},
                "routing_keys": {
                    "training_code_execute": "training.code.execute",
                    "task_status": "task.status.update",
                    "task_log": "task.log",
                    "model_registered": "model.registered",
                },
            },
            "model-training-runtime": {"enabled": True, "execution": {"enabled": True}},
        }
        with patch.dict(os.environ, {}, clear=True), patch(
            "mq_consumer.load_platform_config",
            return_value=platform_config,
        ):
            settings = TrainingCodeConsumer()._settings()

        self.assertEqual(settings["host"], "127.0.0.1")
        self.assertEqual(settings["username"], "automl")
        self.assertEqual(settings["password"], "automl123456")
        self.assertEqual(settings["execute_queue"], "training.code.execute")
        self.assertEqual(settings["task_status_routing_key"], "task.status.update")

    def test_runtime_can_override_shared_queue_with_flat_configuration(self) -> None:
        platform_config = {
            "rabbitmq": {
                "host": "127.0.0.1",
                "username": "automl",
                "password": "automl123456",
                "queues": {"training_code_execute": "shared.queue"},
            },
            "model-training-runtime": {
                "rabbitmq": {"training_code_execute_queue": "runtime.queue"},
            },
        }
        with patch.dict(os.environ, {}, clear=True), patch(
            "mq_consumer.load_platform_config",
            return_value=platform_config,
        ):
            settings = TrainingCodeConsumer()._settings()

        self.assertEqual(settings["execute_queue"], "runtime.queue")

    def test_registers_pytorch_onnx_classification_as_deployable_model(self) -> None:
        consumer = TrainingCodeConsumer()
        model = SimpleNamespace(
            task_kind="classification",
            class_names=["negative", "positive"],
            framework=SimpleNamespace(id="pytorch"),
        )
        outcome = SimpleNamespace(
            result=SimpleNamespace(model=model, metrics={"train_loss": 0.25}),
            artifacts=(
                SimpleNamespace(
                    artifact=SimpleNamespace(
                        deployable=True,
                        role=SimpleNamespace(value="model"),
                        format="onnx",
                    ),
                    object=SimpleNamespace(object_key="runtime/smoke-model.onnx"),
                ),
                SimpleNamespace(
                    artifact=SimpleNamespace(
                        deployable=False,
                        role=SimpleNamespace(value="checkpoint"),
                        format="pt",
                    ),
                    object=SimpleNamespace(object_key="runtime/smoke-model.pt"),
                ),
            ),
        )
        submission = SimpleNamespace(
            package=SimpleNamespace(key="pytorch-smoke-classifier"),
            execution_id="execution-1",
        )

        with patch.object(consumer, "_publish") as publish:
            consumer._publish_deployable_model(7, submission, outcome)

        payload = publish.call_args.args[1]
        self.assertEqual(payload["message_type"], "model.registered")
        self.assertEqual(payload["model_info"]["onnx_save_path"], "runtime/smoke-model.onnx")
        self.assertEqual(payload["model_info"]["runtime_template"], "onnx_classification")

    def test_uses_ultralytics_template_only_for_ultralytics_classification(self) -> None:
        self.assertEqual(
            _runtime_template(
                SimpleNamespace(
                    task_kind="classification",
                    framework=SimpleNamespace(id="ultralytics"),
                )
            ),
            "ultralytics_classification",
        )
