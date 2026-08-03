"""
全局配置管理
优先从 Nacos 获取，回退到环境变量
"""
import os
from typing import Optional

from pydantic import BaseModel, Field
from loguru import logger

from .nacos_config_center import get_config_center
from app import __version__

_last_nacos_log_keys: Optional[tuple[str, ...]] = None
DEFAULT_TRAINING_RUNTIME_IDS = [
    "ultralytics-8.3.0-pytorch-2.5-cu124",
    "pytorch-2.5-cu124",
]


class DatabaseConfig(BaseModel):
    """数据库配置"""
    host: str = "localhost"
    port: int = 3306
    username: str = "root"  # for test
    password: str = "root123456"  # for test
    database: str = "auto_ml"

    @property
    def url(self) -> str:
        return f"mysql+aiomysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class NacosConfig(BaseModel):
    """Nacos 配置"""
    server_addr: str = "127.0.0.1:8848"
    namespace: str = "public"
    data_id: str = "AUTO_ML_CONFIG"
    group: str = "AUTO_ML"


class ModelTrainerConfig(BaseModel):
    """Model Trainer 服务配置"""
    base_url: str = "http://127.0.0.1:8081"
    timeout: int = 30


class ModelDeployConfig(BaseModel):
    """Model Deploy 服务配置"""
    base_url: str = "http://127.0.0.1:8082"
    timeout: int = 60


class AiPipelineRuntimeConfig(BaseModel):
    """AI Pipeline Runtime 服务配置"""
    base_url: str = "http://ai-pipeline-runtime:8010"
    timeout: int = 120


class TrainingCodeRuntimeConfig(BaseModel):
    """Experimental training-code runtime; disabled until explicitly enabled."""

    enabled: bool = False
    base_url: str = ""
    timeout: int = 120
    token: str = ""
    execution_enabled: bool = False
    execution_runtime_ids: list[str] = Field(
        default_factory=lambda: list(DEFAULT_TRAINING_RUNTIME_IDS)
    )
    allow_script_managed_data: bool = False


class Settings(BaseModel):
    """全局设置"""
    # 服务配置
    app_name: str = "AutoML Studio"
    app_version: str = __version__
    host: str = "0.0.0.0"
    port: int = 45678
    debug: bool = False
    task_stale_timeout_seconds: int = 7200
    pipeline_batch_secret_key: str = ""
    assistant_secret_key: str = ""

    # 子配置
    database: DatabaseConfig = DatabaseConfig()
    nacos: NacosConfig = NacosConfig()
    model_trainer: ModelTrainerConfig = ModelTrainerConfig()
    model_deploy: ModelDeployConfig = ModelDeployConfig()
    ai_pipeline_runtime: AiPipelineRuntimeConfig = AiPipelineRuntimeConfig()
    training_code_runtime: TrainingCodeRuntimeConfig = TrainingCodeRuntimeConfig()


def _load_from_nacos(nacos_config: NacosConfig) -> dict:
    """从 Nacos 加载配置"""
    try:
        config = get_config_center().get_config_data()
        return config or {}
    except Exception as e:
        logger.warning(f"Failed to load config from Nacos: {e}")
        return {}


def _extract_db_config(nacos_data: dict) -> dict:
    """从 Nacos 的 db 配置中提取数据库连接信息"""
    db_config = nacos_data.get("db")
    if isinstance(db_config, dict) and db_config:
        return db_config
    return {}


def _load_settings() -> Settings:
    """加载配置"""
    # 1. 先从环境变量加载 Nacos 配置
    nacos_config = NacosConfig(
        server_addr=os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848"),
        namespace=os.getenv("NACOS_NAMESPACE", "public"),
        data_id=os.getenv("NACOS_DATA_ID", "AUTO_ML_CONFIG"),
        group=os.getenv("NACOS_GROUP", "AUTO_ML"),
    )

    # 2. 尝试从 Nacos 加载配置
    use_nacos = os.getenv("USE_NACOS", "true").lower() == "true"
    nacos_data = {}
    if use_nacos:
        nacos_data = _load_from_nacos(nacos_config)
        global _last_nacos_log_keys
        keys = tuple(sorted(str(key) for key in nacos_data.keys()))
        if keys and keys != _last_nacos_log_keys:
            logger.info(f"Loaded config from Nacos: {list(keys)}")
        _last_nacos_log_keys = keys

    # 3. 合并配置：环境变量 > Nacos > DatabaseConfig 默认值
    _db_defaults = DatabaseConfig()
    db_nacos = _extract_db_config(nacos_data)
    database = DatabaseConfig(
        host=os.getenv("DB_HOST", db_nacos.get("host", _db_defaults.host)),
        port=int(os.getenv("DB_PORT", db_nacos.get("port", _db_defaults.port))),
        username=os.getenv("DB_USERNAME", db_nacos.get(
            "username", _db_defaults.username)),
        password=os.getenv("DB_PASSWORD", db_nacos.get(
            "password", _db_defaults.password)),
        database=os.getenv("DB_NAME", db_nacos.get(
            "database", _db_defaults.database)),
    )

    trainer_nacos = nacos_data.get("model-trainer", {})
    model_trainer = ModelTrainerConfig(
        base_url=os.getenv(
            "MODEL_TRAINER_URL",
            trainer_nacos.get("base_url", "http://127.0.0.1:8081"),
        ),
        timeout=int(os.getenv(
            "MODEL_TRAINER_TIMEOUT",
            trainer_nacos.get("timeout", 30),
        )),
    )

    deploy_nacos = nacos_data.get("model-deploy", {})
    model_deploy = ModelDeployConfig(
        base_url=os.getenv(
            "MODEL_DEPLOY_URL",
            deploy_nacos.get("base_url", "http://127.0.0.1:8082"),
        ),
        timeout=int(os.getenv(
            "MODEL_DEPLOY_TIMEOUT",
            deploy_nacos.get("timeout", 60),
        )),
    )

    runtime_nacos = nacos_data.get("ai-pipeline-runtime", {})
    if not isinstance(runtime_nacos, dict) or not runtime_nacos:
        runtime_nacos = nacos_data.get("auto-augment-pipeline", {})
    ai_pipeline_runtime = AiPipelineRuntimeConfig(
        base_url=os.getenv(
            "AI_PIPELINE_RUNTIME_URL",
            os.getenv(
                "AUTO_AUGMENT_PIPELINE_URL",
                runtime_nacos.get("base_url", "http://ai-pipeline-runtime:8010"),
            ),
        ),
        timeout=int(os.getenv(
            "AI_PIPELINE_RUNTIME_TIMEOUT",
            os.getenv(
                "AUTO_AUGMENT_PIPELINE_TIMEOUT",
                runtime_nacos.get("timeout", 120),
            ),
        )),
    )

    training_code_runtime_nacos = nacos_data.get(
        "model-training-runtime",
        nacos_data.get("training-code-runtime", {}),
    )
    if not isinstance(training_code_runtime_nacos, dict):
        training_code_runtime_nacos = {}
    training_code_runtime_execution = training_code_runtime_nacos.get("execution", {})
    if not isinstance(training_code_runtime_execution, dict):
        training_code_runtime_execution = {}
    runtime_ids = training_code_runtime_execution.get(
        "runtime_ids", DEFAULT_TRAINING_RUNTIME_IDS
    )
    if isinstance(runtime_ids, str):
        runtime_ids = [runtime_ids]
    if not isinstance(runtime_ids, list):
        runtime_ids = []
    training_code_runtime = TrainingCodeRuntimeConfig(
        # This experimental integration is centrally managed through Nacos.
        enabled=training_code_runtime_nacos.get("enabled", False),
        base_url=str(training_code_runtime_nacos.get("base_url", "") or ""),
        timeout=training_code_runtime_nacos.get("timeout", 120),
        token=str(training_code_runtime_nacos.get("token", "") or ""),
        execution_enabled=training_code_runtime_execution.get("enabled", False),
        execution_runtime_ids=[
            str(runtime_id).strip()
            for runtime_id in runtime_ids
            if isinstance(runtime_id, str) and runtime_id.strip()
        ],
        allow_script_managed_data=bool(
            training_code_runtime_nacos.get("allow_script_managed_data", False)
        ),
    )

    task_stale_timeout_seconds = int(
        os.getenv(
            "TASK_STALE_TIMEOUT_SECONDS",
            nacos_data.get("task_stale_timeout_seconds", 7200),
        )
    )
    pipeline_batch_nacos = nacos_data.get("ai-pipeline-batch", {})
    if not isinstance(pipeline_batch_nacos, dict):
        pipeline_batch_nacos = {}
    pipeline_batch_secret_key = str(pipeline_batch_nacos.get("secret_key", "") or "")
    assistant_nacos = nacos_data.get("assistant", {})
    if not isinstance(assistant_nacos, dict):
        assistant_nacos = {}
    assistant_secret_key = str(
        assistant_nacos.get("secret_key") or pipeline_batch_secret_key
    )

    return Settings(
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "45678")),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        task_stale_timeout_seconds=task_stale_timeout_seconds,
        pipeline_batch_secret_key=pipeline_batch_secret_key,
        assistant_secret_key=assistant_secret_key,
        database=database,
        nacos=nacos_config,
        model_trainer=model_trainer,
        model_deploy=model_deploy,
        ai_pipeline_runtime=ai_pipeline_runtime,
        training_code_runtime=training_code_runtime,
    )


def get_settings() -> Settings:
    """获取全局配置（单例）"""
    return _load_settings()
