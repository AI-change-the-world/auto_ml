"""
常量定义
"""
from enum import IntEnum


class StorageType(IntEnum):
    """存储类型"""
    LOCAL = 0
    S3 = 1
    WEBDAV = 2


class DataType(IntEnum):
    """数据类型"""
    IMAGE = 0
    TEXT = 1
    VIDEO = 2
    AUDIO = 3


class AnnotationType(IntEnum):
    """标注类型"""
    DETECTION = 0   # 检测
    CLASSIFICATION = 1  # 分类
    SEGMENTATION = 2    # 分割


class TaskType(IntEnum):
    """任务类型"""
    DETECTION = 0
    CLASSIFICATION = 1


class TaskStatus(IntEnum):
    """任务状态"""
    PENDING = 0     # 待处理
    RUNNING = 1     # 运行中
    POST_PROCESS = 2    # 后处理
    COMPLETED = 3   # 完成
    FAILED = 4      # 失败


class MessageType:
    """消息类型常量"""
    TASK_STATUS_UPDATE = "task.status.update"
    TASK_LOG = "task.log"
    MODEL_REGISTERED = "model.registered"
    MODEL_DEPLOYED = "model.deployed"
    MODEL_UNDEPLOYED = "model.undeployed"
    SERVICE_HEARTBEAT = "service.heartbeat"
