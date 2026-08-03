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
    training_code_execute_queue: str = "training.code.execute"
    assist_rpc_queue: str = "auto_ml.assist.rpc"
    pipeline_batch_execute_queue: str = "auto_ml.pipeline.batch.execute"
    pipeline_batch_progress_queue: str = "auto_ml.pipeline.batch.progress"
    pipeline_batch_result_queue: str = "auto_ml.pipeline.batch.result"

    # 路由键
    task_status_routing_key: str = "task.status.update"
    task_log_routing_key: str = "task.log"
    model_registered_routing_key: str = "model.registered"
    model_deployed_routing_key: str = "model.deployed"
    model_undeployed_routing_key: str = "model.undeployed"
    trainer_task_routing_key: str = "trainer.task.submit"
    training_code_execute_routing_key: str = "training.code.execute"
    assist_rpc_routing_key: str = "assist.rpc.request"
    pipeline_batch_execute_routing_key: str = "pipeline.batch.execute"
    pipeline_batch_progress_routing_key: str = "pipeline.batch.progress"
    pipeline_batch_result_routing_key: str = "pipeline.batch.result"


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
            training_code_execute_queue=_get_mq_nested_value(
                mq, "queues", "training_code_execute", "training_code_execute_queue", "training.code.execute"),
            assist_rpc_queue=_get_mq_nested_value(
                mq, "queues", "assist_rpc", "assist_rpc_queue", "auto_ml.assist.rpc"),
            pipeline_batch_execute_queue=_get_mq_nested_value(
                mq, "queues", "pipeline_batch_execute", "pipeline_batch_execute_queue", "auto_ml.pipeline.batch.execute"),
            pipeline_batch_progress_queue=_get_mq_nested_value(
                mq, "queues", "pipeline_batch_progress", "pipeline_batch_progress_queue", "auto_ml.pipeline.batch.progress"),
            pipeline_batch_result_queue=_get_mq_nested_value(
                mq, "queues", "pipeline_batch_result", "pipeline_batch_result_queue", "auto_ml.pipeline.batch.result"),
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
            training_code_execute_routing_key=_get_mq_nested_value(
                mq, "routing_keys", "training_code_execute", "training_code_execute_routing_key", "training.code.execute"),
            assist_rpc_routing_key=_get_mq_nested_value(
                mq, "routing_keys", "assist_rpc", "assist_rpc_routing_key", "assist.rpc.request"),
            pipeline_batch_execute_routing_key=_get_mq_nested_value(
                mq, "routing_keys", "pipeline_batch_execute", "pipeline_batch_execute_routing_key", "pipeline.batch.execute"),
            pipeline_batch_progress_routing_key=_get_mq_nested_value(
                mq, "routing_keys", "pipeline_batch_progress", "pipeline_batch_progress_routing_key", "pipeline.batch.progress"),
            pipeline_batch_result_routing_key=_get_mq_nested_value(
                mq, "routing_keys", "pipeline_batch_result", "pipeline_batch_result_routing_key", "pipeline.batch.result"),
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
        training_code_execute_queue=os.getenv("TRAINING_CODE_EXECUTE_QUEUE", "training.code.execute"),
        assist_rpc_queue=os.getenv("ASSIST_RPC_QUEUE", "auto_ml.assist.rpc"),
        pipeline_batch_execute_queue=os.getenv("PIPELINE_BATCH_EXECUTE_QUEUE", "auto_ml.pipeline.batch.execute"),
        pipeline_batch_progress_queue=os.getenv("PIPELINE_BATCH_PROGRESS_QUEUE", "auto_ml.pipeline.batch.progress"),
        pipeline_batch_result_queue=os.getenv("PIPELINE_BATCH_RESULT_QUEUE", "auto_ml.pipeline.batch.result"),
        task_status_routing_key=os.getenv("TASK_STATUS_ROUTING_KEY", "task.status.update"),
        task_log_routing_key=os.getenv("TASK_LOG_ROUTING_KEY", "task.log"),
        model_registered_routing_key=os.getenv("MODEL_REGISTERED_ROUTING_KEY", "model.registered"),
        model_deployed_routing_key=os.getenv("MODEL_DEPLOYED_ROUTING_KEY", "model.deployed"),
        model_undeployed_routing_key=os.getenv("MODEL_UNDEPLOYED_ROUTING_KEY", "model.undeployed"),
        trainer_task_routing_key=os.getenv("TRAINER_TASK_ROUTING_KEY", "trainer.task.submit"),
        training_code_execute_routing_key=os.getenv("TRAINING_CODE_EXECUTE_ROUTING_KEY", "training.code.execute"),
        assist_rpc_routing_key=os.getenv("ASSIST_RPC_ROUTING_KEY", "assist.rpc.request"),
        pipeline_batch_execute_routing_key=os.getenv("PIPELINE_BATCH_EXECUTE_ROUTING_KEY", "pipeline.batch.execute"),
        pipeline_batch_progress_routing_key=os.getenv("PIPELINE_BATCH_PROGRESS_ROUTING_KEY", "pipeline.batch.progress"),
        pipeline_batch_result_routing_key=os.getenv("PIPELINE_BATCH_RESULT_ROUTING_KEY", "pipeline.batch.result"),
    )


def get_mq_config() -> RabbitMQConfig:
    """获取 RabbitMQ 配置"""
    use_nacos = os.getenv("USE_NACOS", "true").lower() == "true"
    if use_nacos:
        return _load_mq_from_nacos()
    return _load_mq_from_env()
