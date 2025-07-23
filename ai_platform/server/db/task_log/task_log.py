from sqlalchemy import TIMESTAMP, Column, Integer, String, func

from db import Base  # 复用 Base


class TaskLog(Base):
    __tablename__ = "task_log"
    __table_args__ = {"comment": "log of tasks"}

    task_id = Column(Integer, primary_key=True, comment="task id")
    log_content = Column(String(1024), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
