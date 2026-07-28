"""
RabbitMQ 消息消费者
消费来自 model_trainer 和 model_deploy 的消息，写入数据库
"""
import asyncio
import json
import threading
from typing import Callable, Dict, Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel
from loguru import logger

from app.config.nacos_config_center import get_config_center
from app.config.rabbitmq_config import get_mq_config, RabbitMQConfig
from .messages import (
    MessageType, TaskStatusMessage, TaskLogMessage,
    ModelRegisteredMessage, ModelDeployedMessage, ModelUndeployedMessage,
    PipelineBatchProgressMessage, PipelineBatchResultMessage,
)


class MessageConsumer:
    """
    RabbitMQ 消息消费者
    在后台线程中运行，消费消息并调用对应的处理器
    """

    def __init__(self, config: RabbitMQConfig = None):
        self.config = config or get_mq_config()
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._handlers: Dict[str, Callable] = {}
        self._async_handlers: Dict[str, Callable] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._config_lock = threading.RLock()
        self._ready_event = threading.Event()
        self._last_error: Optional[Exception] = None
        get_config_center().register_callback(
            "automl_server_mq_consumer",
            self._on_config_update,
        )

    def _connect(self):
        """建立连接"""
        try:
            with self._config_lock:
                self.config = get_mq_config()
            credentials = pika.PlainCredentials(
                self.config.username,
                self.config.password
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

            # 声明交换机
            self.channel.exchange_declare(
                exchange=self.config.exchange_name,
                exchange_type=self.config.exchange_type,
                durable=True,
            )

            # 声明并绑定队列
            self._setup_queues()
            self._last_error = None
            self._ready_event.set()

            logger.info(
                f"Consumer connected to RabbitMQ: {self.config.host}:{self.config.port}")
        except Exception as e:
            self._last_error = e
            self._ready_event.clear()
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def _on_config_update(self, old_config: dict, new_config: dict):
        old_mq = (old_config or {}).get("rabbitmq", {})
        new_mq = (new_config or {}).get("rabbitmq", {})
        if old_mq == new_mq:
            return

        logger.info("RabbitMQ config changed, consumer will reconnect")
        self._close_connection()

    def _close_connection(self):
        if self.channel and not self.channel.is_closed:
            try:
                self.channel.close()
            except Exception:
                pass
        if self.connection and not self.connection.is_closed:
            try:
                self.connection.close()
            except Exception:
                pass
        self.channel = None
        self.connection = None
        self._ready_event.clear()

    def _setup_queues(self):
        """设置队列和绑定"""
        queue_bindings = [
            (self.config.task_status_queue, self.config.task_status_routing_key),
            (self.config.task_log_queue, self.config.task_log_routing_key),
            (self.config.model_registered_queue,
             self.config.model_registered_routing_key),
            (self.config.model_deployed_queue,
             self.config.model_deployed_routing_key),
            (self.config.model_undeployed_queue,
             self.config.model_undeployed_routing_key),
            (self.config.pipeline_batch_progress_queue,
             self.config.pipeline_batch_progress_routing_key),
            (self.config.pipeline_batch_result_queue,
             self.config.pipeline_batch_result_routing_key),
        ]

        for queue_name, routing_key in queue_bindings:
            # 声明队列
            self.channel.queue_declare(queue=queue_name, durable=True)
            # 绑定到交换机
            self.channel.queue_bind(
                queue=queue_name,
                exchange=self.config.exchange_name,
                routing_key=routing_key,
            )
            logger.debug(f"Queue {queue_name} bound to {routing_key}")

    def register_handler(self, message_type: str, handler: Callable, is_async: bool = False):
        """注册消息处理器"""
        if is_async:
            self._async_handlers[message_type] = handler
        else:
            self._handlers[message_type] = handler
        logger.info(
            f"Registered handler for {message_type} (async={is_async})")

    def _process_message(self, ch, method, properties, body):
        """处理消息"""
        try:
            data = json.loads(body)
            message_type = data.get("message_type", "")

            logger.debug(f"Received message: {message_type}")

            # 解析消息
            message = self._parse_message(message_type, data)
            if message is None:
                logger.warning(f"Unknown message type: {message_type}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # 调用处理器
            if message_type in self._async_handlers:
                # 异步处理器
                handler = self._async_handlers[message_type]
                if self._loop:
                    future = asyncio.run_coroutine_threadsafe(
                        handler(message), self._loop
                    )
                    future.result(timeout=60)  # 等待完成
            elif message_type in self._handlers:
                # 同步处理器
                self._handlers[message_type](message)
            else:
                logger.warning(f"No handler for message type: {message_type}")

            # 确认消息
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # 拒绝消息，不重新入队（避免死循环）
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _parse_message(self, message_type: str, data: dict):
        """解析消息"""
        parsers = {
            MessageType.TASK_STATUS_UPDATE.value: TaskStatusMessage,
            MessageType.TASK_LOG.value: TaskLogMessage,
            MessageType.MODEL_REGISTERED.value: ModelRegisteredMessage,
            MessageType.MODEL_DEPLOYED.value: ModelDeployedMessage,
            MessageType.MODEL_UNDEPLOYED.value: ModelUndeployedMessage,
            MessageType.PIPELINE_BATCH_PROGRESS.value: PipelineBatchProgressMessage,
            MessageType.PIPELINE_BATCH_RESULT.value: PipelineBatchResultMessage,
        }
        parser = parsers.get(message_type)
        if parser:
            return parser(**data)
        return None

    def _consume_loop(self):
        """消费循环"""
        try:
            self._connect()

            # 设置 QoS
            self.channel.basic_qos(prefetch_count=10)

            # 订阅所有队列
            queues = [
                self.config.task_status_queue,
                self.config.task_log_queue,
                self.config.model_registered_queue,
                self.config.model_deployed_queue,
                self.config.model_undeployed_queue,
                self.config.pipeline_batch_progress_queue,
                self.config.pipeline_batch_result_queue,
            ]

            for queue in queues:
                self.channel.basic_consume(
                    queue=queue,
                    on_message_callback=self._process_message,
                    auto_ack=False,
                )

            logger.info("Consumer started, waiting for messages...")

            while self._running:
                self.connection.process_data_events(time_limit=1)

        except Exception as e:
            logger.error(f"Consumer error: {e}")
            if self._running:
                # 尝试重连
                import time
                time.sleep(5)
                self._consume_loop()

    def start(self, event_loop: asyncio.AbstractEventLoop = None):
        """启动消费者（在后台线程中）"""
        if self._running:
            logger.warning("Consumer already running")
            return

        self._running = True
        self._loop = event_loop
        self._ready_event.clear()
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._thread.start()
        logger.info("Message consumer started in background thread")

    def wait_until_ready(self, timeout: float) -> bool:
        return self._ready_event.wait(timeout=timeout)

    @property
    def last_error(self) -> Optional[Exception]:
        return self._last_error

    def stop(self):
        """停止消费者"""
        self._running = False
        get_config_center().unregister_callback("automl_server_mq_consumer")
        self._close_connection()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("Message consumer stopped")


# 单例
_consumer: Optional[MessageConsumer] = None


def get_consumer() -> MessageConsumer:
    """获取消费者单例"""
    global _consumer
    if _consumer is None:
        _consumer = MessageConsumer()
    return _consumer
