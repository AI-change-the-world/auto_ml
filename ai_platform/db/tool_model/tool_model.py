from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from db import Base


class ToolModel(Base):
    __tablename__ = "tool_model"

    id = Column("tool_model_id", Integer, primary_key=True, autoincrement=True)
    name = Column("tool_model_name", String)
    description = Column("tool_model_description", String)
    type = Column("tool_model_type", Integer)  # 0: llm, 1: M-LLM, 2: vision, 3: others
    is_embedded = Column("is_embedded", Integer)  # 0: embedded, 1: remote
    created_at = Column("created_at", DateTime, default=datetime.utcnow)
    updated_at = Column(
        "updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_deleted = Column("is_deleted", Integer, default=0)
    base_url = Column("base_url", String)
    api_key = Column("api_key", String)
    model_name = Column("model_name", String)
