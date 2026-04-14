"""
RabbitMQ 配置
"""
import os
from functools import lru_cache

import yaml
from pydantic import BaseModel
from loguru import logger


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


def _load_mq_from_nacos() -> RabbitMQConfig:
    """从 Nacos 加载 RabbitMQ 配置"""
    try:
        import nacos

        nacos_addr = os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848")
        nacos_namespace = os.getenv("NACOS_NAMESPACE", "public")
        data_id = os.getenv("NACOS_DATA_ID", "AUTO_ML_CONFIG")
        group = os.getenv("NACOS_GROUP", "AUTO_ML")

        client = nacos.NacosClient(nacos_addr, namespace=nacos_namespace)
        config_str = client.get_config(data_id, group)
        config = yaml.safe_load(config_str) or {}

        mq = config.get("rabbitmq", {})
        queues = mq.get("queues", {})

        return RabbitMQConfig(
            host=mq.get("host", "localhost"),
            port=mq.get("port", 5672),
            username=mq.get("username", "guest"),
            password=mq.get("password", "guest"),
            virtual_host=mq.get("virtual_host", "/"),
            exchange_name=mq.get("exchange_name", "auto_ml_exchange"),
            exchange_type=mq.get("exchange_type", "topic"),
            task_status_queue=queues.get("task_status", "auto_ml.task.status"),
            task_log_queue=queues.get("task_log", "auto_ml.task.log"),
            model_registered_queue=queues.get(
                "model_registered", "auto_ml.model.registered"),
            model_deployed_queue=queues.get(
                "model_deployed", "auto_ml.model.deployed"),
            trainer_task_queue=queues.get("trainer_task", "trainer.task.queue"),
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
        trainer_task_queue=os.getenv("TRAINER_TASK_QUEUE", "trainer.task.queue"),
        trainer_task_routing_key=os.getenv("TRAINER_TASK_ROUTING_KEY", "trainer.task.submit"),
    )


@lru_cache(maxsize=1)
def get_mq_config() -> RabbitMQConfig:
    """获取 RabbitMQ 配置"""
    use_nacos = os.getenv("USE_NACOS", "true").lower() == "true"
    if use_nacos:
        return _load_mq_from_nacos()
    return _load_mq_from_env()
