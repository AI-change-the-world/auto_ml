"""
AI Pipeline 相关模型
"""
from sqlalchemy import Column, BigInteger, String, Integer, Float, Text, Boolean, DateTime

from .base_entity import BaseEntity


class AiPipelineTemplate(BaseEntity):
    """AI Pipeline 模板主表"""
    __tablename__ = "ai_pipeline_template"

    template_key = Column(String(128), nullable=False, unique=True, comment="模板稳定标识")
    name = Column(String(255), nullable=False, comment="模板名称")
    description = Column(Text, nullable=True, comment="模板描述")
    scene_type = Column(String(64), nullable=False, comment="场景类型")
    input_kind = Column(String(64), nullable=True, comment="主输入类型")
    output_kind = Column(String(64), nullable=True, comment="主输出类型")
    status = Column(String(32), nullable=False, default="draft", comment="状态: draft/published/disabled")
    latest_version = Column(Integer, nullable=False, default=1, comment="最新版本号")
    published_version = Column(Integer, nullable=True, comment="当前发布版本号")
    is_builtin = Column(Boolean, nullable=False, default=False, comment="是否系统内置模板")
    created_by = Column(String(64), nullable=True, comment="创建人")


class AiPipelineTemplateVersion(BaseEntity):
    """AI Pipeline 模板版本表"""
    __tablename__ = "ai_pipeline_template_version"

    template_id = Column(BigInteger, nullable=False, index=True, comment="模板ID")
    version = Column(Integer, nullable=False, comment="版本号")
    definition_json = Column(Text, nullable=True, comment="模板 DSL JSON")
    form_schema_json = Column(Text, nullable=True, comment="表单 Schema JSON")
    change_note = Column(String(512), nullable=True, comment="变更说明")
    is_published = Column(Boolean, nullable=False, default=False, comment="是否已发布")
    created_by = Column(String(64), nullable=True, comment="创建人")


class AiPipelineBinding(BaseEntity):
    """AI Pipeline 业务绑定表"""
    __tablename__ = "ai_pipeline_binding"

    binding_type = Column(String(64), nullable=False, comment="绑定对象类型")
    binding_target_id = Column(BigInteger, nullable=False, index=True, comment="绑定对象ID")
    template_id = Column(BigInteger, nullable=False, index=True, comment="模板ID")
    template_version = Column(Integer, nullable=False, comment="模板版本")
    name = Column(String(255), nullable=True, comment="绑定名称")
    description = Column(Text, nullable=True, comment="绑定说明")
    is_default = Column(Boolean, nullable=False, default=False, comment="是否默认绑定")
    runtime_input_defaults_json = Column(Text, nullable=True, comment="默认运行参数 JSON")
    resource_bindings_json = Column(Text, nullable=True, comment="资源绑定 JSON")
    created_by = Column(String(64), nullable=True, comment="创建人")


class AiPipelineProviderResource(BaseEntity):
    """AI Provider 资源表"""
    __tablename__ = "ai_pipeline_provider_resource"

    resource_id = Column(String(128), nullable=False, unique=True, index=True, comment="资源稳定标识")
    provider_name = Column(String(128), nullable=False, unique=True, index=True, comment="运行时 provider 名称")
    display_name = Column(String(255), nullable=False, comment="展示名称")
    description = Column(Text, nullable=True, comment="资源描述")
    kind = Column(String(64), nullable=False, comment="provider 类型")
    role = Column(String(64), nullable=False, comment="provider 角色")
    base_url = Column(String(512), nullable=True, comment="provider base url")
    api_key = Column(Text, nullable=True, comment="provider api key")
    model = Column(String(255), nullable=True, comment="provider model")
    timeout_seconds = Column(Float, nullable=False, default=60.0, comment="超时时间")
    temperature = Column(Float, nullable=False, default=0.0, comment="默认温度")
    max_tokens = Column(Integer, nullable=False, default=1024, comment="默认最大 token")
    extra_headers_json = Column(Text, nullable=True, comment="额外请求头 JSON")
    extra_json = Column(Text, nullable=True, comment="额外配置 JSON")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    created_by = Column(String(64), nullable=True, comment="创建人")


class AiPipelineRun(BaseEntity):
    """AI Pipeline 运行主表"""
    __tablename__ = "ai_pipeline_run"

    run_id = Column(String(64), nullable=False, unique=True, comment="外部运行ID")
    template_id = Column(BigInteger, nullable=False, index=True, comment="模板ID")
    template_version = Column(Integer, nullable=False, comment="模板版本")
    binding_id = Column(BigInteger, nullable=True, index=True, comment="绑定ID")
    source_type = Column(String(64), nullable=True, comment="触发来源类型")
    source_id = Column(BigInteger, nullable=True, comment="触发来源ID")
    trigger_mode = Column(String(32), nullable=False, default="sync", comment="触发方式: sync/async")
    execution_mode = Column(String(32), nullable=False, default="interactive", comment="执行模式: interactive/batch/video")
    status = Column(String(32), nullable=False, default="pending", comment="状态: pending/queued/running/succeeded/failed/canceled")
    progress = Column(Integer, nullable=False, default=0, comment="进度 0-100")
    data_inputs_json = Column(Text, nullable=True, comment="数据输入 JSON")
    runtime_inputs_json = Column(Text, nullable=True, comment="运行参数 JSON")
    resource_bindings_json = Column(Text, nullable=True, comment="执行时资源绑定快照 JSON")
    result_summary_json = Column(Text, nullable=True, comment="结果摘要 JSON")
    error_message = Column(Text, nullable=True, comment="错误信息")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    finished_at = Column(DateTime, nullable=True, comment="结束时间")
    created_by = Column(String(64), nullable=True, comment="触发人")


class AiPipelineRunStep(BaseEntity):
    """AI Pipeline 步骤运行表"""
    __tablename__ = "ai_pipeline_run_step"

    run_id = Column(BigInteger, nullable=False, index=True, comment="运行主表ID")
    step_key = Column(String(128), nullable=False, comment="步骤Key")
    step_name = Column(String(255), nullable=True, comment="步骤名称")
    step_type = Column(String(64), nullable=True, comment="步骤类型")
    executor = Column(String(128), nullable=True, comment="执行器名称")
    status = Column(String(32), nullable=False, default="pending", comment="步骤状态")
    attempt_count = Column(Integer, nullable=False, default=0, comment="尝试次数")
    input_ref_json = Column(Text, nullable=True, comment="输入引用 JSON")
    output_ref_json = Column(Text, nullable=True, comment="输出引用 JSON")
    error_message = Column(Text, nullable=True, comment="错误信息")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    finished_at = Column(DateTime, nullable=True, comment="结束时间")


class AiPipelineArtifact(BaseEntity):
    """AI Pipeline 产物索引表"""
    __tablename__ = "ai_pipeline_artifact"

    run_id = Column(BigInteger, nullable=False, index=True, comment="运行主表ID")
    run_step_id = Column(BigInteger, nullable=True, index=True, comment="步骤运行ID")
    artifact_key = Column(String(128), nullable=True, comment="产物Key")
    artifact_type = Column(String(64), nullable=False, comment="产物类型")
    storage_type = Column(String(32), nullable=False, comment="存储类型")
    bucket_name = Column(String(128), nullable=True, comment="Bucket名称")
    object_key = Column(String(512), nullable=True, comment="对象路径")
    content_type = Column(String(128), nullable=True, comment="内容类型")
    size_bytes = Column(BigInteger, nullable=True, comment="大小字节数")
    metadata_json = Column(Text, nullable=True, comment="扩展元数据 JSON")


class AiPipelineEventLog(BaseEntity):
    """AI Pipeline 事件日志表"""
    __tablename__ = "ai_pipeline_event_log"

    run_id = Column(BigInteger, nullable=False, index=True, comment="运行主表ID")
    event_type = Column(String(64), nullable=False, comment="事件类型")
    event_payload = Column(Text, nullable=True, comment="事件内容 JSON")
