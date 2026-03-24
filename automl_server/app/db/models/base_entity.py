"""
基础实体类
包含通用字段：id, created_at, updated_at, is_deleted
"""
from datetime import datetime

from sqlalchemy import Column, BigInteger, DateTime, Boolean
from sqlalchemy.orm import declared_attr

from app.config.database import Base


class BaseEntity(Base):
    """基础实体类"""
    __abstract__ = True

    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment="主键ID")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now, comment="更新时间")
    is_deleted = Column(Boolean, default=False, comment="逻辑删除标记")

    @declared_attr
    def __tablename__(cls):
        """自动生成表名（类名转下划线）"""
        import re
        name = cls.__name__
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
