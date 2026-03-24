"""
数据集相关模型
"""
from sqlalchemy import Column, BigInteger, String, Integer, Text

from .base_entity import BaseEntity


class Dataset(BaseEntity):
    """数据集实体"""
    __tablename__ = "dataset"

    name = Column(String(255), nullable=False, comment="数据集名称")
    storage_type = Column(Integer, default=1,
                          comment="存储类型: 0=本地, 1=S3, 2=WebDAV")
    data_type = Column(Integer, default=0,
                       comment="数据类型: 0=图像, 1=文本, 2=视频, 3=音频")
    save_path = Column(String(512), nullable=True, comment="存储路径")
    count = Column(Integer, default=0, comment="文件数量")
    description = Column(Text, nullable=True, comment="描述")


class DatasetFile(BaseEntity):
    """数据集文件实体"""
    __tablename__ = "dataset_file"

    dataset_id = Column(BigInteger, nullable=False,
                        index=True, comment="数据集ID")
    file_name = Column(String(255), nullable=False, comment="文件名")
    save_path = Column(String(512), nullable=True, comment="存储路径")
