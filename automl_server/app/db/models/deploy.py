"""
模型部署相关模型
"""
from sqlalchemy import Column, BigInteger, String, Integer, Text, Float, Boolean

from .base_entity import BaseEntity


class AvailableModel(BaseEntity):
    """可用模型实体"""
    __tablename__ = "available_model"

    name = Column(String(255), nullable=True, comment="模型名称")
    model_path = Column(String(512), nullable=True, comment="模型路径")
    onnx_model_path = Column(String(512), nullable=True, comment="ONNX模型路径")
    model_type = Column(String(50), nullable=True, comment="模型类型")
    dataset_id = Column(BigInteger, nullable=True,
                        index=True, comment="关联数据集ID")
    task_id = Column(BigInteger, nullable=True, index=True, comment="关联任务ID")
    loss = Column(Float, nullable=True, comment="训练损失")

    # 部署状态
    is_deployed = Column(Boolean, default=False, comment="是否已部署")
    deployment_id = Column(String(100), nullable=True, comment="部署ID")
    deployment_port = Column(Integer, nullable=True, comment="部署端口")
    deployment_version = Column(String(50), nullable=True, comment="部署版本")
    deployment_device = Column(String(50), nullable=True, comment="部署设备")
