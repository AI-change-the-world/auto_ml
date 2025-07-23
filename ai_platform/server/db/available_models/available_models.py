from sqlalchemy import Column, DateTime, Float, Integer, String, func

from db import Base  # 共用 Base


class AvailableModel(Base):
    __tablename__ = "available_models"
    __table_args__ = {"comment": "Available model record"}

    available_model_id = Column(
        Integer, primary_key=True, autoincrement=True, comment="主键 ID"
    )
    save_path = Column(String, nullable=True, comment="保存路径")
    base_model_name = Column(String, nullable=True, comment="基础模型名")
    loss = Column(Float, nullable=True, comment="loss 值")
    epoch = Column(Integer, nullable=True, comment="训练轮数")
    dataset_id = Column(Integer, nullable=True, comment="数据集 ID")
    annotation_id = Column(Integer, nullable=True, comment="标注 ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    is_deleted = Column(Integer, default=0, comment="逻辑删除标志")
    model_type = Column(String, nullable=True, comment="模型类型", default="detection")
