"""
常量定义
"""
from dataclasses import dataclass
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


class DatasetScenarioType(IntEnum):
    """数据集场景类型"""
    NORMAL = 0
    AERIAL_STITCH = 1
    LLM_CONVERSATION = 2
    MLLM_CONVERSATION = 3


class AnnotationType(IntEnum):
    """标注类型"""
    DETECTION = 0   # 检测
    CLASSIFICATION = 1  # 分类
    SEGMENTATION = 2    # 分割
    MLLM = 3
    POSE = 4
    LLM = 5


@dataclass(frozen=True)
class AnnotationTypeDefinition:
    """标注类型元数据，前端通过接口复用这份定义。"""
    value: int
    code: str
    label: str
    color: str
    icon_key: str
    supports_classes: bool


ANNOTATION_TYPE_DEFINITIONS: tuple[AnnotationTypeDefinition, ...] = (
    AnnotationTypeDefinition(
        value=AnnotationType.DETECTION,
        code="detection",
        label="检测",
        color="blue",
        icon_key="bbox",
        supports_classes=True,
    ),
    AnnotationTypeDefinition(
        value=AnnotationType.CLASSIFICATION,
        code="classification",
        label="分类",
        color="green",
        icon_key="classification",
        supports_classes=True,
    ),
    AnnotationTypeDefinition(
        value=AnnotationType.SEGMENTATION,
        code="segmentation",
        label="分割",
        color="orange",
        icon_key="polygon",
        supports_classes=True,
    ),
    AnnotationTypeDefinition(
        value=AnnotationType.MLLM,
        code="mllm",
        label="MLLM",
        color="purple",
        icon_key="mllm",
        supports_classes=False,
    ),
    AnnotationTypeDefinition(
        value=AnnotationType.POSE,
        code="pose",
        label="姿态",
        color="cyan",
        icon_key="pose",
        supports_classes=True,
    ),
    AnnotationTypeDefinition(
        value=AnnotationType.LLM,
        code="llm",
        label="LLM",
        color="geekblue",
        icon_key="llm",
        supports_classes=False,
    ),
)


def get_annotation_type_definitions() -> list[AnnotationTypeDefinition]:
    return list(ANNOTATION_TYPE_DEFINITIONS)


def get_annotation_type_definition(annotation_type: int) -> AnnotationTypeDefinition | None:
    for definition in ANNOTATION_TYPE_DEFINITIONS:
        if definition.value == annotation_type:
            return definition
    return None


class TaskType(IntEnum):
    """任务类型"""
    DETECTION = 0
    CLASSIFICATION = 1
    SEGMENTATION = 2
    POSE = 3


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
