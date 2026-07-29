"""Batch annotation sandbox models."""
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint

from .base_entity import BaseEntity


class AiPipelineBatchRun(BaseEntity):
    """A durable batch script execution requested from a dataset."""

    __tablename__ = "ai_pipeline_batch_run"

    run_id = Column(String(64), nullable=False, unique=True, index=True, comment="外部运行ID")
    batch_group_id = Column(String(64), nullable=True, index=True, comment="连续增量批量标注分组ID")
    dataset_id = Column(BigInteger, nullable=False, index=True, comment="数据集ID")
    annotation_id = Column(BigInteger, nullable=False, index=True, comment="标注项目ID")
    script_key = Column(String(128), nullable=False, comment="脚本标识")
    script_version = Column(String(64), nullable=False, comment="脚本版本")
    script_package_path = Column(String(512), nullable=True, comment="脚本包对象路径快照")
    script_entrypoint = Column(String(255), nullable=True, comment="脚本入口文件快照")
    status = Column(String(32), nullable=False, default="queued", comment="queued/running/succeeded/failed/canceled")
    selection_mode = Column(String(32), nullable=False, default="all", comment="all/unannotated/selected")
    overwrite_policy = Column(String(32), nullable=False, default="skip_existing", comment="skip_existing/overwrite_draft/overwrite_all")
    batch_size = Column(Integer, nullable=False, default=20, comment="单次脚本输入样本数")
    parallelism = Column(Integer, nullable=False, default=1, comment="同一任务并行批次数")
    total_count = Column(Integer, nullable=False, default=0, comment="总样本数")
    succeeded_count = Column(Integer, nullable=False, default=0, comment="成功样本数")
    failed_count = Column(Integer, nullable=False, default=0, comment="失败样本数")
    skipped_count = Column(Integer, nullable=False, default=0, comment="跳过样本数")
    canceled_count = Column(Integer, nullable=False, default=0, comment="取消样本数")
    progress = Column(Integer, nullable=False, default=0, comment="进度 0-100")
    cancel_requested = Column(Boolean, nullable=False, default=False, comment="是否请求取消")
    script_params_json = Column(Text, nullable=True, comment="脚本参数快照 JSON")
    annotation_snapshot_json = Column(Text, nullable=True, comment="标注配置快照 JSON")
    error_message = Column(Text, nullable=True, comment="任务错误")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    finished_at = Column(DateTime, nullable=True, comment="结束时间")


class AiPipelineBatchRunItem(BaseEntity):
    """A snapshot of one sample in a batch annotation run."""

    __tablename__ = "ai_pipeline_batch_run_item"
    __table_args__ = (
        UniqueConstraint("batch_run_id", "sample_item_id", name="uk_ai_pipeline_batch_run_item_sample"),
    )

    batch_run_id = Column(BigInteger, nullable=False, index=True, comment="批量任务主表ID")
    sample_item_id = Column(BigInteger, nullable=False, index=True, comment="样本ID")
    item_key = Column(String(255), nullable=False, comment="样本业务键快照")
    asset_path = Column(String(512), nullable=True, comment="数据集对象路径快照")
    asset_mime_type = Column(String(128), nullable=True, comment="资源 MIME 快照")
    input_snapshot_json = Column(Text, nullable=True, comment="脚本输入快照 JSON")
    chunk_key = Column(String(96), nullable=True, index=True, comment="MQ 批次标识")
    status = Column(String(32), nullable=False, default="pending", comment="pending/queued/succeeded/failed/skipped/canceled")
    attempt_count = Column(Integer, nullable=False, default=0, comment="派发次数")
    annotation_record_id = Column(BigInteger, nullable=True, index=True, comment="写入后的标注记录ID")
    result_json = Column(Text, nullable=True, comment="脚本结果快照 JSON")
    error_message = Column(Text, nullable=True, comment="错误信息")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    finished_at = Column(DateTime, nullable=True, comment="结束时间")


class AiPipelineBatchRunEvent(BaseEntity):
    """Persisted progress and diagnostic events for a batch run."""

    __tablename__ = "ai_pipeline_batch_run_event"

    batch_run_id = Column(BigInteger, nullable=False, index=True, comment="批量任务主表ID")
    event_type = Column(String(64), nullable=False, comment="queued/progress/result/failed/canceled")
    event_payload = Column(Text, nullable=True, comment="事件内容 JSON")


class AiPipelineBatchScript(BaseEntity):
    """A user-managed archive that can be executed by the batch sandbox."""

    __tablename__ = "ai_pipeline_batch_script"

    script_key = Column(String(128), nullable=False, unique=True, index=True, comment="脚本标识")
    version = Column(String(64), nullable=False, comment="脚本版本")
    name = Column(String(255), nullable=False, comment="脚本名称")
    description = Column(Text, nullable=True, comment="脚本描述")
    package_object_key = Column(String(512), nullable=False, comment="ZIP 脚本包对象路径")
    package_file_name = Column(String(255), nullable=False, comment="上传文件名")
    entrypoint = Column(String(255), nullable=False, comment="ZIP 内 Python 入口文件")
    supported_data_types_json = Column(Text, nullable=False, comment="兼容数据类型 JSON")
    supported_annotation_types_json = Column(Text, nullable=False, comment="兼容标注类型 JSON")
    parameter_fields_json = Column(Text, nullable=False, comment="运行参数 Schema JSON")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否允许创建新任务")


class AiPipelineBatchBuiltinScriptSetting(BaseEntity):
    """Persistent enabled state for platform-provided batch scripts."""

    __tablename__ = "ai_pipeline_batch_builtin_script_setting"

    script_key = Column(String(128), nullable=False, unique=True, index=True, comment="内置脚本标识")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否允许创建新任务")
