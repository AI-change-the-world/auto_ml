"""
工具模型
"""
from sqlalchemy import Column, String, Text

from .base_entity import BaseEntity


class ToolModel(BaseEntity):
    """工具模型实体"""
    __tablename__ = "tool_model"

    name = Column(String(255), nullable=False, comment="模型名称")
    model_type = Column(String(50), nullable=True, comment="模型类型")
    endpoint = Column(String(512), nullable=True, comment="服务端点")
    config = Column(Text, nullable=True, comment="配置 JSON")
