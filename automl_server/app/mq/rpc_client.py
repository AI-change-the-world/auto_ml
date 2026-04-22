"""
RabbitMQ RPC client for synchronous assist requests.
"""
import json
import uuid
from typing import Any

import pika
from loguru import logger

from app.config.rabbitmq_config import get_mq_config


class RabbitMQRpcClient:
    def call(self, payload: dict[str, Any], timeout: float = 120) -> dict[str, Any]:
        config = get_mq_config()
        credentials = pika.PlainCredentials(
            config.username,
            config.password,
        )
        parameters = pika.ConnectionParameters(
            host=config.host,
            port=config.port,
            virtual_host=config.virtual_host,
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=max(300, int(timeout) + 30),
        )

        connection = None
        channel = None
        correlation_id = str(uuid.uuid4())
        response_payload: dict[str, Any] | None = None
        callback_queue = None

        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.exchange_declare(
                exchange=config.exchange_name,
                exchange_type=config.exchange_type,
                durable=True,
            )

            result = channel.queue_declare(queue="", exclusive=True, auto_delete=True)
            callback_queue = result.method.queue

            def on_response(ch, method, properties, body):
                nonlocal response_payload
                if properties.correlation_id != correlation_id:
                    return
                try:
                    response_payload = json.loads(body)
                except Exception as exc:
                    response_payload = {"success": False, "error": f"invalid rpc response: {exc}"}

            channel.basic_consume(
                queue=callback_queue,
                on_message_callback=on_response,
                auto_ack=True,
            )
            channel.basic_publish(
                exchange=config.exchange_name,
                routing_key=config.assist_rpc_routing_key,
                body=json.dumps(payload, ensure_ascii=False),
                properties=pika.BasicProperties(
                    reply_to=callback_queue,
                    correlation_id=correlation_id,
                    content_type="application/json",
                    delivery_mode=2,
                ),
            )

            waited = 0.0
            while response_payload is None and waited < timeout:
                connection.process_data_events(time_limit=1)
                waited += 1

            if response_payload is None:
                raise TimeoutError("assist RPC request timed out")
            if not response_payload.get("success", False):
                raise RuntimeError(response_payload.get("error") or "assist RPC request failed")
            return response_payload.get("data")
        except Exception as exc:
            logger.error(f"Assist RPC request failed: {exc}")
            raise
        finally:
            if channel and callback_queue:
                try:
                    channel.queue_delete(queue=callback_queue)
                except Exception:
                    pass
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


_assist_rpc_client: RabbitMQRpcClient | None = None


def get_assist_rpc_client() -> RabbitMQRpcClient:
    global _assist_rpc_client
    if _assist_rpc_client is None:
        _assist_rpc_client = RabbitMQRpcClient()
    return _assist_rpc_client
