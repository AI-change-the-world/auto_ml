from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String

from db import Base  # 共用 Base


class Dataset(Base):
    __tablename__ = "dataset"
    __table_args__ = {"comment": "dataset table"}

    id = Column("dataset_id", BigInteger, primary_key=True, autoincrement=True)
    name = Column("dataset_name", String)
    description = Column(String, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_deleted = Column(Integer, default=0)
    type = Column(
        "dataset_type", Integer, comment="0:image 1:text 2:video 3:audio 4:other"
    )
    ranking = Column(Float, default=0)
    storage_type = Column(Integer, nullable=True)
    url = Column(String, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    scan_status = Column(
        Integer, nullable=True, comment="0: scanning, 1: success, 2: failed"
    )
    file_count = Column(BigInteger, nullable=True)
    sample_file_path = Column(String, nullable=True)
