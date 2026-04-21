"""
模型部署相关模型
"""
from sqlalchemy import Column, BigInteger, String, Integer, Text, Float, Boolean, DateTime

from .base_entity import BaseEntity


class AvailableModel(BaseEntity):
    """可用模型实体"""
    __tablename__ = "available_model"

    name = Column(String(255), nullable=True, comment="模型名称")
    model_path = Column(String(512), nullable=True, comment="模型路径")
    onnx_model_path = Column(String(512), nullable=True, comment="ONNX模型路径")
    model_type = Column(String(50), nullable=True, comment="模型类型")
    class_names = Column(Text, nullable=True, comment="类别名称 JSON")
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
    deployed_at = Column(DateTime, nullable=True, comment="最近一次部署时间")
    inference_count = Column(BigInteger, default=0, nullable=False, comment="累计推理调用次数")
    last_inference_at = Column(DateTime, nullable=True, comment="最近一次推理时间")


class ModelInferenceLog(BaseEntity):
    """模型推理调用记录"""
    __tablename__ = "model_inference_log"

    model_id = Column(BigInteger, nullable=False, index=True, comment="模型ID")
    request_type = Column(String(32), nullable=True, comment="请求方式: file/base64")
    success = Column(Boolean, default=False, nullable=False, comment="是否成功")
    duration_ms = Column(Integer, nullable=True, comment="推理耗时毫秒")
    result_count = Column(Integer, default=0, nullable=False, comment="返回结果数量")
    image_width = Column(Integer, nullable=True, comment="图像宽度")
    image_height = Column(Integer, nullable=True, comment="图像高度")
    error_message = Column(Text, nullable=True, comment="错误信息")
    client_ip = Column(String(64), nullable=True, comment="客户端IP")
