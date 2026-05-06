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
    DPO_PREFERENCE = 4
    DPO_PAIRWISE = 5
    DPO_BEST_OF_N = 6
    DPO_REFERENCE_CHOICE = 7
    DPO_MULTI_TURN = 8


class AnnotationType(IntEnum):
    """标注类型"""
    DETECTION = 0   # 检测
    CLASSIFICATION = 1  # 分类
    SEGMENTATION = 2    # 分割
    MLLM = 3
    POSE = 4
    LLM = 5
    DPO = 6
    DPO_PAIRWISE = 7
    DPO_BEST_OF_N = 8
    DPO_REFERENCE_CHOICE = 9
    DPO_MULTI_TURN = 10


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
    AnnotationTypeDefinition(
        value=AnnotationType.DPO,
        code="dpo",
        label="DPO 兼容",
        color="gold",
        icon_key="dpo",
        supports_classes=False,
    ),
    AnnotationTypeDefinition(
        value=AnnotationType.DPO_PAIRWISE,
        code="dpo_pairwise",
        label="DPO 二选一",
        color="gold",
        icon_key="dpo",
        supports_classes=False,
    ),
    AnnotationTypeDefinition(
        value=AnnotationType.DPO_BEST_OF_N,
        code="dpo_best_of_n",
        label="DPO 多选一",
        color="gold",
        icon_key="dpo",
        supports_classes=False,
    ),
    AnnotationTypeDefinition(
        value=AnnotationType.DPO_REFERENCE_CHOICE,
        code="dpo_reference_choice",
        label="DPO 参考增强",
        color="gold",
        icon_key="dpo",
        supports_classes=False,
    ),
    AnnotationTypeDefinition(
        value=AnnotationType.DPO_MULTI_TURN,
        code="dpo_multi_turn",
        label="DPO 多轮对话",
        color="gold",
        icon_key="dpo",
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


LEGACY_DPO_DATASET_SCENARIOS: tuple[int, ...] = (
    DatasetScenarioType.DPO_PREFERENCE,
)

SPLIT_DPO_DATASET_SCENARIOS: tuple[int, ...] = (
    DatasetScenarioType.DPO_PAIRWISE,
    DatasetScenarioType.DPO_BEST_OF_N,
    DatasetScenarioType.DPO_REFERENCE_CHOICE,
    DatasetScenarioType.DPO_MULTI_TURN,
)

DPO_DATASET_SCENARIOS: tuple[int, ...] = (
    *LEGACY_DPO_DATASET_SCENARIOS,
    *SPLIT_DPO_DATASET_SCENARIOS,
)

LEGACY_DPO_ANNOTATION_TYPES: tuple[int, ...] = (
    AnnotationType.DPO,
)

SPLIT_DPO_ANNOTATION_TYPES: tuple[int, ...] = (
    AnnotationType.DPO_PAIRWISE,
    AnnotationType.DPO_BEST_OF_N,
    AnnotationType.DPO_REFERENCE_CHOICE,
    AnnotationType.DPO_MULTI_TURN,
)

DPO_ANNOTATION_TYPES: tuple[int, ...] = (
    *LEGACY_DPO_ANNOTATION_TYPES,
    *SPLIT_DPO_ANNOTATION_TYPES,
)


def is_dpo_dataset_scenario(scenario_type: int) -> bool:
    return scenario_type in DPO_DATASET_SCENARIOS


def is_split_dpo_dataset_scenario(scenario_type: int) -> bool:
    return scenario_type in SPLIT_DPO_DATASET_SCENARIOS


def is_dpo_annotation_type(annotation_type: int) -> bool:
    return annotation_type in DPO_ANNOTATION_TYPES


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
