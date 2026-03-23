from sqlalchemy import TIMESTAMP, Column, Float, Integer, String, func

from db.base import Base


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
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    is_deleted = Column(Integer, default=0, comment="逻辑删除标志")
    model_type = Column(String, nullable=True,
                        comment="模型类型", default="detection")


class Deployment(Base):
    __tablename__ = "deployments"
    __table_args__ = {"comment": "Model deployment record"}

    deployment_id = Column(Integer, primary_key=True,
                           autoincrement=True, comment="部署ID")
    model_id = Column(Integer, nullable=False, comment="模型ID")
    model_name = Column(String, nullable=True, comment="模型名称")
    version = Column(String, default="v1", comment="版本")
    status = Column(Integer, default=0,
                    comment="状态: 0-pending, 1-running, 2-stopped, 3-error")
    port = Column(Integer, nullable=True, comment="服务端口号")
    pid = Column(Integer, nullable=True, comment="进程ID")
    replicas = Column(Integer, default=1, comment="实例数")
    device = Column(String, default="cpu", comment="运行设备")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
