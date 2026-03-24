"""
Aether Agent 模型
"""
from sqlalchemy import Column, String, Text

from .base_entity import BaseEntity


class Agent(BaseEntity):
    """Agent 实体"""
    __tablename__ = "agent"
    
    name = Column(String(255), nullable=False, comment="Agent 名称")
    description = Column(Text, nullable=True, comment="描述")
    pipeline_content = Column(Text, nullable=True, comment="工作流 JSON")
