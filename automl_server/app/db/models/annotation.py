"""
标注相关模型
"""
from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime, Index, UniqueConstraint

from .base_entity import BaseEntity


class Annotation(BaseEntity):
    """标注项目实体"""
    __tablename__ = "annotation"

    name = Column(String(255), nullable=False, comment="标注项目名称")
    annotation_type = Column(
        Integer, default=0, comment="标注类型: 0=检测(BBox/OBB), 1=分类, 2=分割(Polygon), 3=MLLM, 4=姿态, 5=LLM")
    classes = Column(Text, nullable=True, comment="分类项 JSON")
    storage_type = Column(Integer, default=1,
                          comment="存储类型: 0=本地, 1=S3, 2=WebDAV")
    save_path = Column(String(512), nullable=True, comment="存储路径")
    prompt = Column(Text, nullable=True, comment="AI 标注提示词")
    assist_pipeline = Column(String(128), nullable=True, comment="默认辅助标注 Pipeline")
    default_ai_pipeline_binding_id = Column(BigInteger, nullable=True, comment="默认 AI Pipeline 绑定ID")
    dataset_id = Column(BigInteger, nullable=True,
                        index=True, comment="关联数据集ID")


class AnnotationRecord(BaseEntity):
    """标注记录实体，表示某个标注项目对一个 SampleItem 的标注结果。"""
    __tablename__ = "annotation_record"

    annotation_id = Column(BigInteger, nullable=False,
                           index=True, comment="标注项目ID")
    sample_item_id = Column(BigInteger, nullable=False,
                            index=True, comment="样本ID")
    annotation_type = Column(Integer, nullable=False,
                             comment="标注类型快照")
    status = Column(String(32), default="draft",
                    comment="状态: draft/saved/reviewed")
    content = Column(Text, nullable=True, comment="标注文件路径")


class AnnotationCollaborator(BaseEntity):
    """匿名协作者。当前没有用户体系，用后端签发 token 标识标注人。"""
    __tablename__ = "annotation_collaborator"

    annotation_id = Column(BigInteger, nullable=False,
                           index=True, comment="标注项目ID")
    display_name = Column(String(64), nullable=False, comment="协作者显示名称")
    token = Column(String(128), nullable=False, unique=True,
                   index=True, comment="协作者访问令牌")
    status = Column(String(32), default="active",
                    comment="状态: active/disabled")
    last_active_at = Column(DateTime, nullable=True, comment="最近活跃时间")


class AnnotationSampleAssignment(BaseEntity):
    """样本协作分配记录。MVP 使用样本级独占分配。"""
    __tablename__ = "annotation_sample_assignment"
    __table_args__ = (
        UniqueConstraint("annotation_id", "sample_item_id",
                         name="uk_annotation_assignment_sample"),
        Index("idx_annotation_assignment_collaborator",
              "annotation_id", "collaborator_id"),
    )

    annotation_id = Column(BigInteger, nullable=False,
                           index=True, comment="标注项目ID")
    sample_item_id = Column(BigInteger, nullable=False,
                            index=True, comment="样本ID")
    collaborator_id = Column(BigInteger, nullable=False,
                             index=True, comment="协作者ID")
    status = Column(String(32), default="assigned",
                    comment="状态: assigned/in_progress/submitted/released")
    lease_expires_at = Column(DateTime, nullable=True, comment="分配锁过期时间")
    submitted_at = Column(DateTime, nullable=True, comment="提交时间")
    collab_state = Column(Text, nullable=True, comment="Yjs 协作文档快照")
