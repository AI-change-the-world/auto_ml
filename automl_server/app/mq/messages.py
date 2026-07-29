"""
消息定义
与 model_trainer/model_deploy 保持一致
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class MessageType(str, Enum):
    """消息类型"""
    TASK_STATUS_UPDATE = "task.status.update"
    TASK_LOG = "task.log"
    MODEL_REGISTERED = "model.registered"
    MODEL_DEPLOYED = "model.deployed"
    MODEL_UNDEPLOYED = "model.undeployed"
    SERVICE_HEARTBEAT = "service.heartbeat"
    PIPELINE_BATCH_PROGRESS = "pipeline.batch.progress"
    PIPELINE_BATCH_RESULT = "pipeline.batch.result"


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
    model_info: Dict[str, Any]
    # model_info 包含:
    # - dataset_id: int
    # - save_path: str
    # - base_model_name: str
    # - loss: float
    # - model_type: str


class ModelDeployedMessage(BaseMessage):
    """模型部署消息"""
    model_id: int
    deployment_info: Dict[str, Any]
    # deployment_info 包含:
    # - deployment_id: str
    # - port: int
    # - version: str
    # - device: str


class ModelUndeployedMessage(BaseMessage):
    """模型卸载消息"""
    model_id: int
    deployment_id: int


class PipelineBatchProgressMessage(BaseMessage):
    run_id: str
    chunk_key: str
    batch_item_id: Optional[int] = None
    processed: int = 0
    total: int = 0
    message: Optional[str] = None
    phase: str = "execution"


class PipelineBatchResultMessage(BaseMessage):
    run_id: str
    chunk_key: str
    results: list[Dict[str, Any]] = []
