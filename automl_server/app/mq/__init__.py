"""RabbitMQ 消息队列模块"""
from .consumer import MessageConsumer, get_consumer
from .publisher import MessagePublisher, get_publisher
from .messages import (
    BaseMessage, TaskStatusMessage, TaskLogMessage,
    ModelRegisteredMessage, ModelDeployedMessage, ModelUndeployedMessage
)

__all__ = [
    "MessageConsumer", "get_consumer",
    "MessagePublisher", "get_publisher",
    "BaseMessage", "TaskStatusMessage", "TaskLogMessage",
    "ModelRegisteredMessage", "ModelDeployedMessage", "ModelUndeployedMessage",
]
