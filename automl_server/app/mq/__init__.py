"""RabbitMQ 消息队列模块"""
from .consumer import MessageConsumer, get_consumer
from .messages import (
    BaseMessage, TaskStatusMessage, TaskLogMessage,
    ModelRegisteredMessage, ModelDeployedMessage, ModelUndeployedMessage
)

__all__ = [
    "MessageConsumer", "get_consumer",
    "BaseMessage", "TaskStatusMessage", "TaskLogMessage",
    "ModelRegisteredMessage", "ModelDeployedMessage", "ModelUndeployedMessage",
]
