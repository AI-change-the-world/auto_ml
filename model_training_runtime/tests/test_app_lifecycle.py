from __future__ import annotations

import unittest
from unittest.mock import patch

from app import app, lifespan


class AppLifecycleTest(unittest.IsolatedAsyncioTestCase):
    async def test_starts_and_stops_mq_consumer_when_execution_is_enabled(self) -> None:
        class FakeConsumer:
            def __init__(self) -> None:
                self.started = False
                self.stopped = False
                self.active_executions = 0

            @property
            def is_running(self) -> bool:
                return self.started and not self.stopped

            @property
            def is_connected(self) -> bool:
                return self.is_running

            def start(self) -> None:
                self.started = True

            def stop(self) -> None:
                self.stopped = True

        consumer = FakeConsumer()
        config = {"enabled": True, "execution": {"enabled": True}}
        with (
            patch("app.TrainingCodeConsumer", return_value=consumer),
            patch("app.load_model_training_runtime_config", return_value=config),
        ):
            async with lifespan(app):
                self.assertIs(app.state.training_code_consumer, consumer)
                self.assertTrue(consumer.started)
                self.assertFalse(consumer.stopped)

        self.assertTrue(consumer.stopped)
        self.assertIsNone(app.state.training_code_consumer)
