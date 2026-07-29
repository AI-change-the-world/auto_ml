import queue
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

try:
    import pika  # noqa: F401
except ModuleNotFoundError:
    PIKA_AVAILABLE = False
else:
    PIKA_AVAILABLE = True


class _FakeConnection:
    is_closed = False

    def close(self):
        self.is_closed = True


class _FakeChannel:
    def __init__(self, failures: int = 0):
        self.is_closed = False
        self.failures = failures
        self.publish_calls = []

    def basic_publish(self, **kwargs):
        self.publish_calls.append(kwargs)
        if len(self.publish_calls) <= self.failures:
            raise RuntimeError("temporary broker failure")

    def close(self):
        self.is_closed = True


class _ConnectedFakeChannel:
    is_closed = False

    def __init__(self):
        self.calls = []

    def exchange_declare(self, **kwargs):
        self.calls.append(("exchange_declare", kwargs))

    def queue_declare(self, **kwargs):
        self.calls.append(("queue_declare", kwargs))

    def queue_bind(self, **kwargs):
        self.calls.append(("queue_bind", kwargs))

    def confirm_delivery(self):
        self.calls.append(("confirm_delivery", {}))


@unittest.skipUnless(PIKA_AVAILABLE, "pika is required for MessagePublisher tests")
class MessagePublisherTest(unittest.TestCase):
    def test_connect_declares_and_binds_execute_queue(self):
        from app.mq.publisher import MessagePublisher

        channel = _ConnectedFakeChannel()
        publisher = MessagePublisher.__new__(MessagePublisher)
        publisher.config = SimpleNamespace(
            host="rabbitmq",
            port=5672,
            username="automl",
            password="password",
            virtual_host="/",
            exchange_name="auto_ml_exchange",
            exchange_type="topic",
            pipeline_batch_execute_queue="auto_ml.pipeline.batch.execute",
            pipeline_batch_execute_routing_key="pipeline.batch.execute",
        )
        publisher._config_lock = threading.RLock()
        publisher._state_lock = threading.RLock()
        publisher._publisher_ready_event = threading.Event()
        publisher._reconnect_requested = threading.Event()

        connection = _FakeConnection()
        connection.channel = lambda: channel
        with (
            patch("app.mq.publisher.get_mq_config", return_value=publisher.config),
            patch("app.mq.publisher.pika.PlainCredentials"),
            patch("app.mq.publisher.pika.ConnectionParameters"),
            patch("app.mq.publisher.pika.BlockingConnection", return_value=connection),
        ):
            publisher._connect()

        self.assertIn(
            ("queue_declare", {"queue": "auto_ml.pipeline.batch.execute", "durable": True}),
            channel.calls,
        )
        self.assertIn(
            (
                "queue_bind",
                {
                    "queue": "auto_ml.pipeline.batch.execute",
                    "exchange": "auto_ml_exchange",
                    "routing_key": "pipeline.batch.execute",
                },
            ),
            channel.calls,
        )
        self.assertIn(("confirm_delivery", {}), channel.calls)

    def test_retries_unconfirmed_publish_with_mandatory_routing(self):
        from app.mq.publisher import MessagePublisher, PublishRequest

        publisher = MessagePublisher.__new__(MessagePublisher)
        first_channel = _FakeChannel(failures=1)
        retry_channel = _FakeChannel()
        publisher.config = SimpleNamespace(exchange_name="auto_ml_exchange")
        publisher.connection = _FakeConnection()
        publisher.channel = first_channel
        publisher._config_lock = threading.RLock()
        publisher._state_lock = threading.RLock()
        publisher._publish_queue = queue.Queue()
        publisher._publisher_stop_event = threading.Event()
        publisher._publisher_ready_event = threading.Event()
        publisher._publisher_ready_event.set()
        publisher._reconnect_requested = threading.Event()

        def reconnect():
            publisher.connection = _FakeConnection()
            publisher.channel = retry_channel
            publisher._publisher_ready_event.set()
            publisher._reconnect_requested.clear()

        publisher._connect = reconnect
        request = PublishRequest("pipeline.batch.execute", "{}", threading.Event())
        publisher._publish_queue.put(request)
        publisher._publish_queue.put(None)

        with patch("app.mq.publisher.time.sleep"):
            publisher._publisher_loop()

        self.assertTrue(request.done.is_set())
        self.assertIsNone(request.error)
        self.assertEqual(first_channel.publish_calls[0]["mandatory"], True)
        self.assertEqual(retry_channel.publish_calls[0]["mandatory"], True)
