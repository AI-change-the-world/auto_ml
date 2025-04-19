from sqlalchemy import TIMESTAMP, Column, Integer, SmallInteger, func

from db import Base


class Task(Base):
    __tablename__ = "task"
    __table_args__ = {"comment": "task table"}

    task_id = Column(Integer, primary_key=True, autoincrement=True, comment="task id")
    task_type = Column(
        Integer, default=0, nullable=True, comment="0 train; 1 eval; 2 others"
    )
    dataset_id = Column(Integer, nullable=False, comment="dataset id")
    annotation_id = Column(Integer, nullable=False, comment="annotation id")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    is_deleted = Column(SmallInteger, default=0, comment="逻辑删除标记")
