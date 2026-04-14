"""
RabbitMQ 消息队列工具类
从 Nacos 获取配置，发送消息到 RabbitMQ
"""
import json
import os
import threading
from datetime import datetime
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Dict, Optional

import pika
import yaml
from pydantic import BaseModel

from utils.logger import logger


# ============ 消息类型定义 ============

class MessageType(str, Enum):
    """消息类型"""
    # 任务状态
    TASK_STATUS_UPDATE = "task.status.update"
    TASK_LOG = "task.log"
    
    # 模型相关
    MODEL_REGISTERED = "model.registered"
    MODEL_DEPLOYED = "model.deployed"
    MODEL_UNDEPLOYED = "model.undeployed"
    
    # 健康检查
    SERVICE_HEARTBEAT = "service.heartbeat"


class TaskStatus(int, Enum):
    """任务状态"""
    PENDING = 0      # 待处理
    RUNNING = 1      # 进行中
    POST_PROCESS = 2 # 后处理
    COMPLETED = 3    # 完成
    FAILED = 4       # 失败


class BaseMessage(BaseModel):
    """基础消息结构"""
    message_type: str
    service_name: str
    timestamp: str = ""
    
    def __init__(self, **data):
        if not data.get("timestamp"):
            data["timestamp"] = datetime.now().isoformat()
        super().__init__(**data)


class TaskStatusMessage(BaseMessage):
    """任务状态更新消息"""
    task_id: int
    status: int
    message: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class TaskLogMessage(BaseMessage):
    """任务日志消息"""
    task_id: int
    log_content: str
    log_level: str = "INFO"


class ModelRegisteredMessage(BaseMessage):
    """模型注册消息"""
    task_id: int
    model_info: Dict[str, Any]  # 包含 save_path, base_model_name, loss, epoch 等


class ModelDeployedMessage(BaseMessage):
    """模型部署消息"""
    model_id: int
    deployment_info: Dict[str, Any]  # 包含 port, version, device 等


class ModelUndeployedMessage(BaseMessage):
    """模型卸载消息"""
    model_id: int
    deployment_id: int


# ============ RabbitMQ 配置 ============

class RabbitMQConfig(BaseModel):
    """RabbitMQ 配置"""
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    virtual_host: str = "/"
    
    # 交换机和队列
    exchange_name: str = "auto_ml_exchange"
    exchange_type: str = "topic"
    
    # 队列名称
    task_queue: str = "auto_ml.task"
    model_queue: str = "auto_ml.model"
    log_queue: str = "auto_ml.log"


def load_rabbitmq_config_from_nacos() -> RabbitMQConfig:
    """从 Nacos 加载 RabbitMQ 配置"""
    try:
        import nacos
        
        nacos_addr = os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848")
        nacos_namespace = os.getenv("NACOS_NAMESPACE", "public")
        data_id = os.getenv("NACOS_DATA_ID", "AUTO_ML_CONFIG")
        group = os.getenv("NACOS_GROUP", "AUTO_ML")
        
        logger.info(f"Loading RabbitMQ config from Nacos: {nacos_addr}, {data_id}, {group}")
        
        client = nacos.NacosClient(nacos_addr, namespace=nacos_namespace)
        config_str = client.get_config(data_id, group)
        config = yaml.safe_load(config_str) or {}

        mq_config = config.get("rabbitmq", {})
        return RabbitMQConfig(
            host=mq_config.get("host", "localhost"),
            port=mq_config.get("port", 5672),
            username=mq_config.get("username", "guest"),
            password=mq_config.get("password", "guest"),
            virtual_host=mq_config.get("virtual_host", "/"),
            exchange_name=mq_config.get("exchange_name", "auto_ml_exchange"),
            exchange_type=mq_config.get("exchange_type", "topic"),
        )
    except Exception as e:
        logger.warning(f"Failed to load from Nacos, using env config: {e}")
        return load_rabbitmq_config_from_env()


def load_rabbitmq_config_from_env() -> RabbitMQConfig:
    """从环境变量加载 RabbitMQ 配置"""
    return RabbitMQConfig(
        host=os.getenv("RABBITMQ_HOST", "localhost"),
        port=int(os.getenv("RABBITMQ_PORT", "5672")),
        username=os.getenv("RABBITMQ_USER", "guest"),
        password=os.getenv("RABBITMQ_PASSWORD", "guest"),
        virtual_host=os.getenv("RABBITMQ_VHOST", "/"),
        exchange_name=os.getenv("RABBITMQ_EXCHANGE", "auto_ml_exchange"),
        exchange_type=os.getenv("RABBITMQ_EXCHANGE_TYPE", "topic"),
    )


@lru_cache(maxsize=1)
def get_mq_config() -> RabbitMQConfig:
    """获取 MQ 配置（优先从 Nacos）"""
    use_nacos = os.getenv("USE_NACOS", "true").lower() == "true"
    if use_nacos:
        return load_rabbitmq_config_from_nacos()
    return load_rabbitmq_config_from_env()


# ============ RabbitMQ 客户端 ============

class RabbitMQClient:
    """RabbitMQ 客户端"""
    
    _instance: Optional["RabbitMQClient"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config = get_mq_config()
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self._connect()
        self._initialized = True
    
    def _connect(self):
        """建立连接"""
        try:
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
            
            logger.info(f"Connected to RabbitMQ: {self.config.host}:{self.config.port}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def _ensure_connection(self):
        """确保连接可用"""
        if self.connection is None or self.connection.is_closed:
            self._connect()
        if self.channel is None or self.channel.is_closed:
            self.channel = self.connection.channel()
    
    def publish(self, routing_key: str, message: BaseMessage):
        """发布消息"""
        try:
            self._ensure_connection()
            
            body = message.model_dump_json()
            
            self.channel.basic_publish(
                exchange=self.config.exchange_name,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 持久化
                    content_type="application/json",
                ),
            )
            
            logger.debug(f"Published message: {routing_key} -> {body[:100]}...")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            # 尝试重连
            self._connect()
            raise
    
    def close(self):
        """关闭连接"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


# ============ 便捷函数 ============

def get_mq_client() -> RabbitMQClient:
    """获取 MQ 客户端单例"""
    return RabbitMQClient()


def publish_task_status(
    task_id: int, 
    status: TaskStatus, 
    service_name: str,
    message: str = None,
    extra_data: Dict[str, Any] = None
):
    """发布任务状态更新"""
    msg = TaskStatusMessage(
        message_type=MessageType.TASK_STATUS_UPDATE,
        service_name=service_name,
        task_id=task_id,
        status=status.value,
        message=message,
        extra_data=extra_data,
    )
    get_mq_client().publish(MessageType.TASK_STATUS_UPDATE, msg)


def publish_task_log(task_id: int, log_content: str, service_name: str, log_level: str = "INFO"):
    """发布任务日志"""
    msg = TaskLogMessage(
        message_type=MessageType.TASK_LOG,
        service_name=service_name,
        task_id=task_id,
        log_content=log_content,
        log_level=log_level,
    )
    get_mq_client().publish(MessageType.TASK_LOG, msg)


def publish_model_registered(task_id: int, model_info: Dict[str, Any], service_name: str):
    """发布模型注册消息"""
    msg = ModelRegisteredMessage(
        message_type=MessageType.MODEL_REGISTERED,
        service_name=service_name,
        task_id=task_id,
        model_info=model_info,
    )
    get_mq_client().publish(MessageType.MODEL_REGISTERED, msg)


def publish_model_deployed(model_id: int, deployment_info: Dict[str, Any], service_name: str):
    """发布模型部署消息"""
    msg = ModelDeployedMessage(
        message_type=MessageType.MODEL_DEPLOYED,
        service_name=service_name,
        model_id=model_id,
        deployment_info=deployment_info,
    )
    get_mq_client().publish(MessageType.MODEL_DEPLOYED, msg)


def publish_model_undeployed(model_id: int, deployment_id: int, service_name: str):
    """发布模型卸载消息"""
    msg = ModelUndeployedMessage(
        message_type=MessageType.MODEL_UNDEPLOYED,
        service_name=service_name,
        model_id=model_id,
        deployment_id=deployment_id,
    )
    get_mq_client().publish(MessageType.MODEL_UNDEPLOYED, msg)
