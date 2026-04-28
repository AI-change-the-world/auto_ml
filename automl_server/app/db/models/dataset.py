"""数据集相关模型"""
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
    scenario_type = Column(Integer, default=0,
                           comment="场景类型: 0=普通, 1=无人机航拍/拼接, 2=LLM对话标注, 3=MLLM对话标注")
    scenario_config = Column(Text, nullable=True, comment="场景配置 JSON")
    save_path = Column(String(512), nullable=True, comment="存储路径")
    count = Column(Integer, default=0, comment="样本数量")
    description = Column(Text, nullable=True, comment="描述")


class Asset(BaseEntity):
    """原始资源实体。图片、视频、文本文件等都先作为 Asset 管理。"""
    __tablename__ = "asset"

    dataset_id = Column(BigInteger, nullable=False,
                        index=True, comment="所属数据集ID")
    asset_type = Column(String(32), nullable=False,
                        comment="资源类型: image/text/video/audio/file")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    save_path = Column(String(512), nullable=True, comment="存储路径")
    mime_type = Column(String(128), nullable=True, comment="MIME 类型")
    size_bytes = Column(BigInteger, nullable=True, comment="文件大小")
    meta_json = Column(Text, nullable=True, comment="资源元数据 JSON")


class SampleItem(BaseEntity):
    """数据集样本实体，是训练和标注的最小业务单元。"""
    __tablename__ = "sample_item"

    dataset_id = Column(BigInteger, nullable=False,
                        index=True, comment="所属数据集ID")
    asset_id = Column(BigInteger, nullable=True,
                      index=True, comment="关联原始资源ID，可为空")
    item_type = Column(String(32), nullable=False,
                       comment="样本类型: image/text/video_frame/conversation/preference")
    item_key = Column(String(255), nullable=False,
                      index=True, comment="样本业务键")
    locator = Column(Text, nullable=True, comment="样本在资源中的定位信息 JSON")
    payload = Column(Text, nullable=True, comment="无文件样本或结构化样本内容 JSON")
    sort_order = Column(Integer, default=0, comment="排序")
