"""
任务相关模型
"""
from sqlalchemy import Column, BigInteger, String, Integer, Text

from .base_entity import BaseEntity


class Task(BaseEntity):
    """训练任务实体"""
    __tablename__ = "task"
    
    task_type = Column(Integer, default=0, comment="任务类型: 0=检测, 1=分类")
    dataset_id = Column(BigInteger, nullable=True, index=True, comment="数据集ID")
    annotation_id = Column(BigInteger, nullable=True, index=True, comment="标注ID")
    status = Column(Integer, default=0, comment="状态: 0=待处理, 1=运行中, 2=后处理, 3=完成, 4=失败")
    config = Column(Text, nullable=True, comment="配置 JSON")
    result = Column(Text, nullable=True, comment="结果 JSON")
    error_message = Column(Text, nullable=True, comment="错误信息")


class TaskLog(BaseEntity):
    """任务日志实体"""
    __tablename__ = "task_log"
    
    task_id = Column(BigInteger, nullable=False, index=True, comment="任务ID")
    content = Column(Text, nullable=True, comment="日志内容")
    log_level = Column(String(20), default="INFO", comment="日志级别")


class BaseModels(BaseEntity):
    """基础模型实体"""
    __tablename__ = "base_models"
    
    name = Column(String(255), nullable=False, comment="模型名称")
    model_type = Column(String(50), nullable=True, comment="模型类型")
    description = Column(Text, nullable=True, comment="描述")
    save_path = Column(String(512), nullable=True, comment="模型路径")
