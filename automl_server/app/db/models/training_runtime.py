"""Catalog records owned by the custom model-training runtime path."""
from sqlalchemy import BigInteger, Boolean, Column, String, Text, UniqueConstraint

from .base_entity import BaseEntity


class TrainingRuntimeCodePackage(BaseEntity):
    """An immutable, runtime-registered release of a user training script ZIP."""

    __tablename__ = "training_runtime_code_package"
    __table_args__ = (
        UniqueConstraint("package_key", "version", name="uk_training_runtime_code_package_release"),
    )

    package_key = Column(String(128), nullable=False, comment="训练脚本标识")
    version = Column(String(64), nullable=False, comment="训练脚本版本")
    name = Column(String(255), nullable=False, comment="展示名称")
    description = Column(Text, nullable=True, comment="描述")
    runtime_id = Column(String(128), nullable=False, comment="平台托管运行时标识")
    entrypoint = Column(String(512), nullable=False, comment="ZIP 内训练入口")
    package_object_key = Column(String(512), nullable=False, comment="不可变 ZIP 对象路径")
    package_sha256 = Column(String(64), nullable=False, comment="ZIP SHA-256")
    package_size_bytes = Column(BigInteger, nullable=False, comment="ZIP 大小")
    package_file_name = Column(String(255), nullable=False, comment="上传文件名")
    supported_tasks_json = Column(Text, nullable=False, comment="支持任务声明 JSON")
    input_modes_json = Column(Text, nullable=False, comment="训练数据输入模式 JSON")
    class_names_json = Column(Text, nullable=False, comment="可选固定类别顺序 JSON")
    parameters_schema_json = Column(Text, nullable=False, comment="脚本参数 Schema JSON")
    model_input_contract_json = Column(Text, nullable=True, comment="模型输入约束 JSON")
    output_contract_json = Column(Text, nullable=False, comment="产物输出约束 JSON")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否允许创建新训练任务")


class TrainingRuntimeModelPackage(BaseEntity):
    """An immutable model ZIP that is selectable only by custom script training."""

    __tablename__ = "training_runtime_model_package"

    name = Column(String(255), nullable=False, comment="展示名称")
    package_object_key = Column(String(512), nullable=False, comment="原始 ZIP 对象路径")
    package_sha256 = Column(String(64), nullable=False, unique=True, comment="原始 ZIP SHA-256")
    package_size_bytes = Column(BigInteger, nullable=False, comment="原始 ZIP 大小")
    package_file_name = Column(String(255), nullable=False, comment="上传文件名")
    task_kind = Column(String(64), nullable=False, comment="任务类型")
    class_names_json = Column(Text, nullable=False, comment="类别顺序 JSON")
    framework_id = Column(String(128), nullable=False, comment="训练框架标识")
    framework_version = Column(String(128), nullable=False, comment="训练框架版本")
    artifact_format = Column(String(64), nullable=False, comment="初始化产物格式")
    initialize_object_key = Column(String(512), nullable=False, comment="初始化权重对象路径")
    initialize_sha256 = Column(String(64), nullable=False, comment="初始化权重 SHA-256")
    initialize_size_bytes = Column(BigInteger, nullable=False, comment="初始化权重大小")
    resume_object_key = Column(String(512), nullable=True, comment="可恢复检查点对象路径")
    resume_sha256 = Column(String(64), nullable=True, comment="可恢复检查点 SHA-256")
    resume_size_bytes = Column(BigInteger, nullable=True, comment="可恢复检查点大小")
    metadata_json = Column(Text, nullable=False, comment="扩展元数据 JSON")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否允许在自定义训练中选择")


class TrainingRuntimeExecution(BaseEntity):
    """Immutable custom-script submission and its worker lifecycle."""

    __tablename__ = "training_runtime_execution"

    task_id = Column(BigInteger, nullable=False, unique=True, comment="平台训练任务ID")
    execution_id = Column(String(36), nullable=False, unique=True, comment="运行执行ID")
    code_package_id = Column(BigInteger, nullable=False, comment="训练脚本包ID")
    model_package_id = Column(BigInteger, nullable=True, comment="可选输入模型包ID")
    input_mode = Column(String(32), nullable=False, comment="数据输入模式")
    submission_json = Column(Text, nullable=False, comment="不可变训练提交 JSON")
    status = Column(String(32), nullable=False, default="queued", comment="运行时执行状态")
    result_json = Column(Text, nullable=True, comment="训练结果和产物 JSON")
    error_message = Column(Text, nullable=True, comment="执行错误")
    model_registered = Column(Boolean, nullable=False, default=False, comment="可部署模型是否已登记")
