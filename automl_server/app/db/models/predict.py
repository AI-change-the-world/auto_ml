"""
预测相关模型
"""
from sqlalchemy import Column, BigInteger, String, Integer, Text

from .base_entity import BaseEntity


class PredictTask(BaseEntity):
    """预测任务实体"""
    __tablename__ = "predict_task"

    task_type = Column(String(50), nullable=True, comment="任务类型")
    source = Column(String(512), nullable=True, comment="输入源")
    result = Column(Text, nullable=True, comment="结果")
    status = Column(Integer, default=0, comment="状态")
    model_id = Column(BigInteger, nullable=True, index=True, comment="使用的模型ID")


class PredictData(BaseEntity):
    """预测数据实体"""
    __tablename__ = "predict_data"

    predict_task_id = Column(BigInteger, nullable=False,
                             index=True, comment="预测任务ID")
    data = Column(Text, nullable=True, comment="预测数据")
