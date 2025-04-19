from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from db import Base  # 复用 Base


class Annotation(Base):
    __tablename__ = "annotation"
    __table_args__ = {"comment": "annotation table"}

    id = Column("annotation_id", BigInteger, primary_key=True, autoincrement=True)
    dataset_id = Column(BigInteger, nullable=True)
    annotation_type = Column(
        Integer, nullable=True, comment="0:分类 1:检测 2:分割 3:其它"
    )
    updated_at = Column(DateTime)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime)
    class_items = Column(String, nullable=True)
    annotation_path = Column(String, nullable=True)
    storage_type = Column(Integer, nullable=True, comment="0:本地 1:s3 2:webdav 3:其它")
