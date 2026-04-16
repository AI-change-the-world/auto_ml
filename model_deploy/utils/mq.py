"""
RabbitMQ 消息队列工具类
从 Nacos 获取配置，发送消息到 RabbitMQ
"""
import os
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import pika
from pydantic import BaseModel

from utils.config_center import get_config_center
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


@dataclass
class PublishRequest:
    routing_key: str
    body: str
    done: threading.Event
    error: Optional[Exception] = None


def load_rabbitmq_config_from_nacos() -> RabbitMQConfig:
    """从 Nacos 加载 RabbitMQ 配置"""
    try:
        config = get_config_center().get_config_data()
        if not config:
            return load_rabbitmq_config_from_env()

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
        self._config_lock = threading.RLock()
        self._state_lock = threading.RLock()
        self._publish_queue: "queue.Queue[Optional[PublishRequest]]" = queue.Queue()
        self._publisher_stop_event = threading.Event()
        self._publisher_ready_event = threading.Event()
        self._reconnect_requested = threading.Event()
        self._publisher_thread = threading.Thread(
            target=self._publisher_loop,
            name="model-deploy-mq-publisher",
            daemon=True,
        )
        self._reconnect_requested.set()
        get_config_center().register_callback(
            "model_deploy_mq_client",
            self._on_config_update,
        )
        self._publisher_thread.start()
        self._initialized = True
    
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
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # 声明交换机
            channel.exchange_declare(
                exchange=self.config.exchange_name,
                exchange_type=self.config.exchange_type,
                durable=True,
            )
            with self._state_lock:
                self.connection = connection
                self.channel = channel
            self._publisher_ready_event.set()
            self._reconnect_requested.clear()
            
            logger.info(f"Connected to RabbitMQ: {self.config.host}:{self.config.port}")
        except Exception as e:
            self._publisher_ready_event.clear()
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def _on_config_update(self, old_config: dict, new_config: dict):
        old_mq = (old_config or {}).get("rabbitmq", {})
        new_mq = (new_config or {}).get("rabbitmq", {})
        if old_mq == new_mq:
            return

        logger.info("RabbitMQ config changed, MQ client will reconnect")
        self._reconnect_requested.set()
    
    def _ensure_connection(self):
        """确保连接可用"""
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
                for attempt in range(1, 3):
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
                        )
                        logger.debug(f"Published message: {request.routing_key} -> {request.body[:100]}...")
                        request.error = None
                        break
                    except Exception as exc:
                        logger.error(f"Failed to publish message: {exc}")
                        self._close_connection()
                        request.error = exc
                        if attempt >= 2:
                            raise
                        time.sleep(0.5)
            except Exception:
                pass
            finally:
                request.done.set()
                self._publish_queue.task_done()

        self._close_connection()
    
    def publish(self, routing_key: str, message: BaseMessage):
        """发布消息"""
        body = message.model_dump_json()
        request = PublishRequest(
            routing_key=str(routing_key),
            body=body,
            done=threading.Event(),
        )
        self._publish_queue.put(request)
        if not request.done.wait(timeout=max(5, int(os.getenv("MQ_PUBLISH_TIMEOUT", "30")))):
            raise TimeoutError(f"Timed out publishing MQ message: {routing_key}")
        if request.error is not None:
            raise request.error
    
    def close(self):
        """关闭连接"""
        try:
            self._publisher_stop_event.set()
            self._publish_queue.put(None)
            if self._publisher_thread.is_alive():
                self._publisher_thread.join(timeout=5)
            self._close_connection()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")

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
    get_mq_client().publish(MessageType.TASK_STATUS_UPDATE.value, msg)


def publish_task_log(task_id: int, log_content: str, service_name: str, log_level: str = "INFO"):
    """发布任务日志"""
    msg = TaskLogMessage(
        message_type=MessageType.TASK_LOG,
        service_name=service_name,
        task_id=task_id,
        log_content=log_content,
        log_level=log_level,
    )
    get_mq_client().publish(MessageType.TASK_LOG.value, msg)


def publish_model_registered(task_id: int, model_info: Dict[str, Any], service_name: str):
    """发布模型注册消息"""
    msg = ModelRegisteredMessage(
        message_type=MessageType.MODEL_REGISTERED,
        service_name=service_name,
        task_id=task_id,
        model_info=model_info,
    )
    get_mq_client().publish(MessageType.MODEL_REGISTERED.value, msg)


def publish_model_deployed(model_id: int, deployment_info: Dict[str, Any], service_name: str):
    """发布模型部署消息"""
    msg = ModelDeployedMessage(
        message_type=MessageType.MODEL_DEPLOYED,
        service_name=service_name,
        model_id=model_id,
        deployment_info=deployment_info,
    )
    get_mq_client().publish(MessageType.MODEL_DEPLOYED.value, msg)


def publish_model_undeployed(model_id: int, deployment_id: int, service_name: str):
    """发布模型卸载消息"""
    msg = ModelUndeployedMessage(
        message_type=MessageType.MODEL_UNDEPLOYED,
        service_name=service_name,
        model_id=model_id,
        deployment_id=deployment_id,
    )
    get_mq_client().publish(MessageType.MODEL_UNDEPLOYED.value, msg)
