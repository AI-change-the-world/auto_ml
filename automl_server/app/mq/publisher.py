"""
RabbitMQ 消息发布器
用于向 model_trainer 下发训练任务
"""
import json
import os
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import pika
from loguru import logger

from app.config.nacos_config_center import get_config_center
from app.config.rabbitmq_config import RabbitMQConfig, get_mq_config


PUBLISH_MAX_ATTEMPTS = 5
PUBLISH_RETRY_INTERVAL_SECONDS = 1


@dataclass
class PublishRequest:
    routing_key: str
    body: str
    done: threading.Event
    error: Optional[Exception] = None


class MessagePublisher:
    """RabbitMQ 消息发布器"""

    def __init__(self, config: RabbitMQConfig = None):
        self.config = config or get_mq_config()
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self._config_lock = threading.RLock()
        self._state_lock = threading.RLock()
        self._publish_queue: "queue.Queue[Optional[PublishRequest]]" = queue.Queue()
        self._publisher_stop_event = threading.Event()
        self._publisher_ready_event = threading.Event()
        self._reconnect_requested = threading.Event()
        self._publisher_thread = threading.Thread(
            target=self._publisher_loop,
            name="automl-server-mq-publisher",
            daemon=True,
        )
        self._reconnect_requested.set()
        get_config_center().register_callback(
            "automl_server_mq_publisher",
            self._on_config_update,
        )
        self._publisher_thread.start()

    def _connect(self):
        try:
            with self._config_lock:
                self.config = get_mq_config()
                credentials = pika.PlainCredentials(
                    self.config.username,
                    self.config.password,
                )
                parameters = pika.ConnectionParameters(
                    host=self.config.host,
                    port=self.config.port,
                    virtual_host=self.config.virtual_host,
                    credentials=credentials,
                    heartbeat=60,
                    blocked_connection_timeout=300,
                )
                connection = pika.BlockingConnection(parameters)
                channel = connection.channel()
                channel.exchange_declare(
                    exchange=self.config.exchange_name,
                    exchange_type=self.config.exchange_type,
                    durable=True,
                )
                channel.queue_declare(
                    queue=self.config.pipeline_batch_execute_queue,
                    durable=True,
                )
                channel.queue_bind(
                    queue=self.config.pipeline_batch_execute_queue,
                    exchange=self.config.exchange_name,
                    routing_key=self.config.pipeline_batch_execute_routing_key,
                )
                channel.queue_declare(
                    queue=self.config.training_code_execute_queue,
                    durable=True,
                )
                channel.queue_bind(
                    queue=self.config.training_code_execute_queue,
                    exchange=self.config.exchange_name,
                    routing_key=self.config.training_code_execute_routing_key,
                )
                # Confirm mode makes a publish wait for the broker acknowledgement.
                # Combined with mandatory=True below, an unbound routing key raises
                # instead of being silently discarded by RabbitMQ.
                channel.confirm_delivery()
            with self._state_lock:
                self.connection = connection
                self.channel = channel
            self._publisher_ready_event.set()
            self._reconnect_requested.clear()
            logger.info(
                f"Publisher connected to RabbitMQ: {self.config.host}:{self.config.port}"
            )
        except Exception as e:
            self._publisher_ready_event.clear()
            logger.error(f"Failed to connect MQ publisher: {e}")
            raise

    def _on_config_update(self, old_config: dict, new_config: dict):
        old_mq = (old_config or {}).get("rabbitmq", {})
        new_mq = (new_config or {}).get("rabbitmq", {})
        if old_mq == new_mq:
            return

        logger.info("RabbitMQ config changed, publisher will reconnect")
        self._reconnect_requested.set()

    def _ensure_connection(self):
        with self._state_lock:
            connection = self.connection
            channel = self.channel
        if (
            self._reconnect_requested.is_set()
            or connection is None
            or channel is None
            or connection.is_closed
            or channel.is_closed
        ):
            self._close_connection()
            self._connect()

    def _close_connection(self):
        with self._state_lock:
            channel = self.channel
            connection = self.connection
            self.channel = None
            self.connection = None
        self._publisher_ready_event.clear()
        if channel and not channel.is_closed:
            try:
                channel.close()
            except Exception:
                pass
        if connection and not connection.is_closed:
            try:
                connection.close()
            except Exception:
                pass

    def _publisher_loop(self):
        while not self._publisher_stop_event.is_set():
            try:
                request = self._publish_queue.get(timeout=1)
            except queue.Empty:
                if self._reconnect_requested.is_set():
                    try:
                        self._ensure_connection()
                    except Exception:
                        time.sleep(1)
                continue

            if request is None:
                self._publish_queue.task_done()
                break

            try:
                for attempt in range(1, PUBLISH_MAX_ATTEMPTS + 1):
                    try:
                        self._ensure_connection()
                        with self._state_lock:
                            channel = self.channel
                        if channel is None:
                            raise RuntimeError("RabbitMQ channel is unavailable")
                        channel.basic_publish(
                            exchange=self.config.exchange_name,
                            routing_key=request.routing_key,
                            body=request.body,
                            properties=pika.BasicProperties(
                                delivery_mode=2,
                                content_type="application/json",
                            ),
                            mandatory=True,
                        )
                        request.error = None
                        break
                    except Exception as exc:
                        logger.warning(
                            "Failed to publish RabbitMQ message: routing_key=%s attempt=%s/%s error=%s",
                            request.routing_key,
                            attempt,
                            PUBLISH_MAX_ATTEMPTS,
                            exc,
                        )
                        self._close_connection()
                        request.error = exc
                        if attempt >= PUBLISH_MAX_ATTEMPTS:
                            raise
                        time.sleep(PUBLISH_RETRY_INTERVAL_SECONDS)
            except Exception:
                pass
            finally:
                request.done.set()
                self._publish_queue.task_done()

        self._close_connection()

    def publish_training_task(self, payload: Dict[str, Any]):
        """发布训练任务到 model_trainer"""
        body = json.dumps(payload, ensure_ascii=False)
        request = PublishRequest(
            routing_key=self.config.trainer_task_routing_key,
            body=body,
            done=threading.Event(),
        )
        self._publish_queue.put(request)
        if not request.done.wait(timeout=max(5, int(os.getenv("MQ_PUBLISH_TIMEOUT", "30")))):
            raise TimeoutError(
                f"Timed out publishing training task: task_id={payload.get('task_id')}"
            )
        if request.error is not None:
            raise request.error
        logger.info(
            f"Published training task: task_id={payload.get('task_id')}, routing_key={self.config.trainer_task_routing_key}"
        )

    def publish_training_code_execution(self, payload: Dict[str, Any]):
        """Publish a frozen custom-script execution to its dedicated worker."""
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        request = PublishRequest(
            routing_key=self.config.training_code_execute_routing_key,
            body=body,
            done=threading.Event(),
        )
        self._publish_queue.put(request)
        if not request.done.wait(timeout=max(5, int(os.getenv("MQ_PUBLISH_TIMEOUT", "30")))):
            raise TimeoutError(
                "Timed out publishing custom training execution: "
                f"task_id={payload.get('task', {}).get('task_id')}"
            )
        if request.error is not None:
            raise request.error
        logger.info(
            "Published custom training execution: task_id=%s execution_id=%s routing_key=%s",
            payload.get("task", {}).get("task_id"),
            payload.get("execution_id"),
            self.config.training_code_execute_routing_key,
        )

    def publish_pipeline_batch_execute(self, payload: Dict[str, Any]):
        body = json.dumps(payload, ensure_ascii=False)
        request = PublishRequest(
            routing_key=self.config.pipeline_batch_execute_routing_key,
            body=body,
            done=threading.Event(),
        )
        self._publish_queue.put(request)
        if not request.done.wait(timeout=max(5, int(os.getenv("MQ_PUBLISH_TIMEOUT", "30")))):
            raise TimeoutError(
                f"Timed out publishing pipeline batch chunk: run_id={payload.get('run_id')}"
            )
        if request.error is not None:
            raise request.error
        logger.info(
            "Published pipeline batch chunk: run_id=%s chunk_key=%s",
            payload.get("run_id"),
            payload.get("chunk_key"),
        )

    def wait_until_ready(self, timeout: float = 5) -> bool:
        if self.is_ready():
            return True
        self._reconnect_requested.set()
        deadline = time.time() + max(0, timeout)
        while time.time() < deadline:
            if self.is_ready():
                return True
            self._publisher_ready_event.wait(timeout=0.2)
        return self.is_ready()

    def close(self):
        try:
            self._publisher_stop_event.set()
            self._publish_queue.put(None)
            if self._publisher_thread.is_alive():
                self._publisher_thread.join(timeout=5)
            self._close_connection()
            get_config_center().unregister_callback("automl_server_mq_publisher")
        except Exception as e:
            logger.error(f"Error closing publisher: {e}")

    def is_ready(self) -> bool:
        with self._state_lock:
            connection = self.connection
            channel = self.channel
        return (
            self._publisher_ready_event.is_set()
            and connection is not None
            and not connection.is_closed
            and channel is not None
            and not channel.is_closed
        )


_publisher: Optional[MessagePublisher] = None


def get_publisher() -> MessagePublisher:
    global _publisher
    if _publisher is None:
        _publisher = MessagePublisher()
    return _publisher
