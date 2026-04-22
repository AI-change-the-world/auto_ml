from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

import pika
import yaml

logger = logging.getLogger(__name__)


@dataclass
class RabbitMQConfig:
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    virtual_host: str = "/"
    exchange_name: str = "auto_ml_exchange"
    exchange_type: str = "topic"
    assist_rpc_queue: str = "auto_ml.assist.rpc"
    assist_rpc_routing_key: str = "assist.rpc.request"


def _get_mq_nested_value(
    mq: dict[str, Any],
    section: str,
    key: str,
    flat_key: str,
    default: str,
) -> str:
    section_value = mq.get(section, {})
    if isinstance(section_value, dict) and section_value.get(key):
        return str(section_value[key])
    if mq.get(flat_key):
        return str(mq[flat_key])
    return default


def _fetch_nacos_payload() -> dict[str, Any]:
    server_addr = os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848")
    namespace = os.getenv("NACOS_NAMESPACE", "public")
    data_id = os.getenv("MQ_NACOS_DATA_ID", os.getenv("AUTO_ML_NACOS_DATA_ID", "AUTO_ML_CONFIG"))
    group = os.getenv("MQ_NACOS_GROUP", os.getenv("NACOS_GROUP", "AUTO_ML"))
    log_dir = os.getenv("MQ_NACOS_LOG_DIR", "/tmp/auto_augment_pipeline/nacos/mq-logs")
    try:
        import nacos

        client = nacos.NacosClient(server_addr, namespace=namespace, logDir=log_dir)
        content = client.get_config(data_id, group) or ""
        if not content:
            raise RuntimeError("Nacos config is empty")
        payload = yaml.safe_load(content) or {}
        if not isinstance(payload, dict):
            raise RuntimeError("Nacos config payload must be a mapping")
        return payload
    except Exception as exc:
        raise RuntimeError(f"Failed to load MQ config from Nacos dataId `{data_id}`: {exc}") from exc


def load_rabbitmq_config_from_nacos_payload(payload: dict[str, Any]) -> RabbitMQConfig:
    mq = payload.get("rabbitmq", {}) if isinstance(payload, dict) else {}
    if not isinstance(mq, dict):
        mq = {}
    return RabbitMQConfig(
        host=str(mq.get("host", "localhost")),
        port=int(mq.get("port", 5672)),
        username=str(mq.get("username", "guest")),
        password=str(mq.get("password", "guest")),
        virtual_host=str(mq.get("virtual_host", "/")),
        exchange_name=str(mq.get("exchange_name", "auto_ml_exchange")),
        exchange_type=str(mq.get("exchange_type", "topic")),
        assist_rpc_queue=_get_mq_nested_value(
            mq, "queues", "assist_rpc", "assist_rpc_queue", "auto_ml.assist.rpc"
        ),
        assist_rpc_routing_key=_get_mq_nested_value(
            mq,
            "routing_keys",
            "assist_rpc",
            "assist_rpc_routing_key",
            "assist.rpc.request",
        ),
    )


def load_rabbitmq_config() -> RabbitMQConfig:
    payload = _fetch_nacos_payload()
    return load_rabbitmq_config_from_nacos_payload(payload)


class RabbitMQRpcWorker:
    def __init__(self, config: RabbitMQConfig, handler) -> None:
        self.config = config
        self.handler = handler
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._connection: pika.BlockingConnection | None = None
        self._channel: pika.adapters.blocking_connection.BlockingChannel | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._consume_loop, name="auto-augment-rpc-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._thread = None

    def _connect(self) -> tuple[pika.BlockingConnection, pika.adapters.blocking_connection.BlockingChannel]:
        credentials = pika.PlainCredentials(self.config.username, self.config.password)
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
        channel.queue_declare(queue=self.config.assist_rpc_queue, durable=True)
        channel.queue_bind(
            queue=self.config.assist_rpc_queue,
            exchange=self.config.exchange_name,
            routing_key=self.config.assist_rpc_routing_key,
        )
        return connection, channel

    def _consume_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                connection, channel = self._connect()
                self._connection = connection
                self._channel = channel
                channel.basic_qos(prefetch_count=4)
                channel.basic_consume(
                    queue=self.config.assist_rpc_queue,
                    on_message_callback=self._on_message,
                    auto_ack=False,
                )
                logger.info("Auto augment MQ RPC worker listening on `%s`", self.config.assist_rpc_queue)
                while not self._stop_event.is_set():
                    connection.process_data_events(time_limit=1)
            except Exception as exc:
                logger.error("Auto augment MQ RPC worker error: %s", exc)
                time.sleep(2)
            finally:
                self._close()

    def _on_message(self, ch, method, properties, body) -> None:
        try:
            payload = json.loads(body)
            result = self.handler(payload)
            response_body = json.dumps({"success": True, "data": result}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("Auto augment MQ RPC handler failed")
            response_body = json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)

        try:
            if properties.reply_to:
                ch.basic_publish(
                    exchange="",
                    routing_key=properties.reply_to,
                    body=response_body,
                    properties=pika.BasicProperties(
                        correlation_id=properties.correlation_id,
                        content_type="application/json",
                        delivery_mode=2,
                    ),
                )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _close(self) -> None:
        channel = self._channel
        connection = self._connection
        self._channel = None
        self._connection = None
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
