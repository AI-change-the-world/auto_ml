"""
RabbitMQ 消息发布器
用于向 model_trainer 下发训练任务
"""
import json
import threading
from typing import Any, Dict, Optional

import pika
from loguru import logger

from app.config.nacos_config_center import get_config_center
from app.config.rabbitmq_config import RabbitMQConfig, get_mq_config


class MessagePublisher:
    """RabbitMQ 消息发布器"""

    def __init__(self, config: RabbitMQConfig = None):
        self.config = config or get_mq_config()
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self._lock = threading.Lock()
        self._config_lock = threading.RLock()
        get_config_center().register_callback(
            "automl_server_mq_publisher",
            self._on_config_update,
        )
        self._connect()

    def _connect(self):
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
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.exchange_declare(
                exchange=self.config.exchange_name,
                exchange_type=self.config.exchange_type,
                durable=True,
            )
            logger.info(
                f"Publisher connected to RabbitMQ: {self.config.host}:{self.config.port}"
            )

    def _on_config_update(self, old_config: dict, new_config: dict):
        old_mq = (old_config or {}).get("rabbitmq", {})
        new_mq = (new_config or {}).get("rabbitmq", {})
        if old_mq == new_mq:
            return

        logger.info("RabbitMQ config changed, publisher will reconnect")
        self.close()

    def _ensure_connection(self):
        if self.connection is None or self.connection.is_closed:
            self._connect()
        if self.channel is None or self.channel.is_closed:
            self.channel = self.connection.channel()

    def publish_training_task(self, payload: Dict[str, Any]):
        """发布训练任务到 model_trainer"""
        body = json.dumps(payload, ensure_ascii=False)
        with self._lock:
            self._ensure_connection()
            self.channel.basic_publish(
                exchange=self.config.exchange_name,
                routing_key=self.config.trainer_task_routing_key,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )
        logger.info(
            f"Published training task: task_id={payload.get('task_id')}, routing_key={self.config.trainer_task_routing_key}"
        )

    def close(self):
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self.channel = None
            self.connection = None
        except Exception as e:
            logger.error(f"Error closing publisher: {e}")


_publisher: Optional[MessagePublisher] = None


def get_publisher() -> MessagePublisher:
    global _publisher
    if _publisher is None:
        _publisher = MessagePublisher()
    return _publisher
