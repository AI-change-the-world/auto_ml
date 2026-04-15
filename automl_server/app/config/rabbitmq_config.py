"""
RabbitMQ 配置
"""
import os

import yaml
from pydantic import BaseModel
from loguru import logger

from .nacos_config_center import get_config_center


class RabbitMQConfig(BaseModel):
    """RabbitMQ 配置"""
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    virtual_host: str = "/"

    # 交换机配置
    exchange_name: str = "auto_ml_exchange"
    exchange_type: str = "topic"

    # 队列名称
    task_status_queue: str = "auto_ml.task.status"
    task_log_queue: str = "auto_ml.task.log"
    model_registered_queue: str = "auto_ml.model.registered"
    model_deployed_queue: str = "auto_ml.model.deployed"
    model_undeployed_queue: str = "auto_ml.model.undeployed"
    heartbeat_queue: str = "auto_ml.heartbeat"
    trainer_task_queue: str = "trainer.task.queue"

    # 路由键
    task_status_routing_key: str = "task.status.update"
    task_log_routing_key: str = "task.log"
    model_registered_routing_key: str = "model.registered"
    model_deployed_routing_key: str = "model.deployed"
    model_undeployed_routing_key: str = "model.undeployed"
    trainer_task_routing_key: str = "trainer.task.submit"


def _get_mq_nested_value(mq: dict, section: str, key: str, flat_key: str, default):
    section_value = mq.get(section, {})
    if isinstance(section_value, dict) and section_value.get(key):
        return section_value[key]
    if mq.get(flat_key):
        return mq[flat_key]
    return default


def _load_mq_from_nacos() -> RabbitMQConfig:
    """从 Nacos 加载 RabbitMQ 配置"""
    try:
        config = get_config_center().get_config_data()
        if not config:
            return _load_mq_from_env()

        mq = config.get("rabbitmq", {})

        return RabbitMQConfig(
            host=mq.get("host", "localhost"),
            port=mq.get("port", 5672),
            username=mq.get("username", "guest"),
            password=mq.get("password", "guest"),
            virtual_host=mq.get("virtual_host", "/"),
            exchange_name=mq.get("exchange_name", "auto_ml_exchange"),
            exchange_type=mq.get("exchange_type", "topic"),
            task_status_queue=_get_mq_nested_value(
                mq, "queues", "task_status", "task_status_queue", "auto_ml.task.status"),
            task_log_queue=_get_mq_nested_value(
                mq, "queues", "task_log", "task_log_queue", "auto_ml.task.log"),
            model_registered_queue=_get_mq_nested_value(
                mq, "queues", "model_registered", "model_registered_queue", "auto_ml.model.registered"),
            model_deployed_queue=_get_mq_nested_value(
                mq, "queues", "model_deployed", "model_deployed_queue", "auto_ml.model.deployed"),
            model_undeployed_queue=_get_mq_nested_value(
                mq, "queues", "model_undeployed", "model_undeployed_queue", "auto_ml.model.undeployed"),
            heartbeat_queue=_get_mq_nested_value(
                mq, "queues", "heartbeat", "heartbeat_queue", "auto_ml.heartbeat"),
            trainer_task_queue=_get_mq_nested_value(
                mq, "queues", "trainer_task", "trainer_task_queue", "trainer.task.queue"),
            task_status_routing_key=_get_mq_nested_value(
                mq, "routing_keys", "task_status", "task_status_routing_key", "task.status.update"),
            task_log_routing_key=_get_mq_nested_value(
                mq, "routing_keys", "task_log", "task_log_routing_key", "task.log"),
            model_registered_routing_key=_get_mq_nested_value(
                mq, "routing_keys", "model_registered", "model_registered_routing_key", "model.registered"),
            model_deployed_routing_key=_get_mq_nested_value(
                mq, "routing_keys", "model_deployed", "model_deployed_routing_key", "model.deployed"),
            model_undeployed_routing_key=_get_mq_nested_value(
                mq, "routing_keys", "model_undeployed", "model_undeployed_routing_key", "model.undeployed"),
            trainer_task_routing_key=_get_mq_nested_value(
                mq, "routing_keys", "trainer_task", "trainer_task_routing_key", "trainer.task.submit"),
        )
    except Exception as e:
        logger.warning(f"Failed to load RabbitMQ config from Nacos: {e}")
        return _load_mq_from_env()


def _load_mq_from_env() -> RabbitMQConfig:
    """从环境变量加载 RabbitMQ 配置"""
    return RabbitMQConfig(
        host=os.getenv("RABBITMQ_HOST", "localhost"),
        port=int(os.getenv("RABBITMQ_PORT", "5672")),
        username=os.getenv("RABBITMQ_USER", "guest"),
        password=os.getenv("RABBITMQ_PASSWORD", "guest"),
        virtual_host=os.getenv("RABBITMQ_VHOST", "/"),
        exchange_name=os.getenv("RABBITMQ_EXCHANGE", "auto_ml_exchange"),
        exchange_type=os.getenv("RABBITMQ_EXCHANGE_TYPE", "topic"),
        task_status_queue=os.getenv("TASK_STATUS_QUEUE", "auto_ml.task.status"),
        task_log_queue=os.getenv("TASK_LOG_QUEUE", "auto_ml.task.log"),
        model_registered_queue=os.getenv("MODEL_REGISTERED_QUEUE", "auto_ml.model.registered"),
        model_deployed_queue=os.getenv("MODEL_DEPLOYED_QUEUE", "auto_ml.model.deployed"),
        model_undeployed_queue=os.getenv("MODEL_UNDEPLOYED_QUEUE", "auto_ml.model.undeployed"),
        heartbeat_queue=os.getenv("HEARTBEAT_QUEUE", "auto_ml.heartbeat"),
        trainer_task_queue=os.getenv("TRAINER_TASK_QUEUE", "trainer.task.queue"),
        task_status_routing_key=os.getenv("TASK_STATUS_ROUTING_KEY", "task.status.update"),
        task_log_routing_key=os.getenv("TASK_LOG_ROUTING_KEY", "task.log"),
        model_registered_routing_key=os.getenv("MODEL_REGISTERED_ROUTING_KEY", "model.registered"),
        model_deployed_routing_key=os.getenv("MODEL_DEPLOYED_ROUTING_KEY", "model.deployed"),
        model_undeployed_routing_key=os.getenv("MODEL_UNDEPLOYED_ROUTING_KEY", "model.undeployed"),
        trainer_task_routing_key=os.getenv("TRAINER_TASK_ROUTING_KEY", "trainer.task.submit"),
    )


def get_mq_config() -> RabbitMQConfig:
    """获取 RabbitMQ 配置"""
    use_nacos = os.getenv("USE_NACOS", "true").lower() == "true"
    if use_nacos:
        return _load_mq_from_nacos()
    return _load_mq_from_env()
