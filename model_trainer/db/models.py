from sqlalchemy import TIMESTAMP, Column, Float, Integer, String, func

from db.base import Base


class Task(Base):
    __tablename__ = "task"
    __table_args__ = {"comment": "task table"}

    task_id = Column(Integer, primary_key=True,
                     autoincrement=True, comment="task id")
    task_type = Column(
        String, default="", nullable=True, comment="0 train; 1 eval; 2 others"
    )
    dataset_id = Column(Integer, nullable=True, comment="dataset id")
    annotation_id = Column(Integer, nullable=True, comment="annotation id")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    is_deleted = Column(Integer, default=0, comment="逻辑删除标记")
    status = Column(
        Integer,
        default=0,
        comment="任务状态, 0 pre task, 1 on task,2 post task,3 done, 4 other",
    )
    task_config = Column(String, nullable=True, comment="任务配置")


class TaskLog(Base):
    __tablename__ = "task_log"
    __table_args__ = {"comment": "log of tasks"}

    id = Column(Integer, primary_key=True,
                autoincrement=True, comment="log id")
    task_id = Column(Integer, nullable=False, comment="task id")
    log_content = Column(String(1024), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")


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
