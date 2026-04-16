"""
全局配置管理
优先从 Nacos 获取，回退到环境变量
"""
import os
import re
from typing import Optional

from pydantic import BaseModel
from loguru import logger

from .nacos_config_center import get_config_center

_last_nacos_log_keys: Optional[tuple[str, ...]] = None


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


class AutoAugmentPipelineConfig(BaseModel):
    """Auto Augment Pipeline 服务配置"""
    base_url: str = "http://auto-augment-pipeline:8010"
    timeout: int = 120
    default_profile: str = "assist_default"


class Settings(BaseModel):
    """全局设置"""
    # 服务配置
    app_name: str = "AutoML Server"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 45678
    debug: bool = False

    # 子配置
    database: DatabaseConfig = DatabaseConfig()
    nacos: NacosConfig = NacosConfig()
    model_trainer: ModelTrainerConfig = ModelTrainerConfig()
    model_deploy: ModelDeployConfig = ModelDeployConfig()
    auto_augment_pipeline: AutoAugmentPipelineConfig = AutoAugmentPipelineConfig()


def _load_from_nacos(nacos_config: NacosConfig) -> dict:
    """从 Nacos 加载配置"""
    try:
        config = get_config_center().get_config_data()
        return config or {}
    except Exception as e:
        logger.warning(f"Failed to load config from Nacos: {e}")
        return {}


def _extract_db_config(nacos_data: dict) -> dict:
    """兼容 db 与 spring.datasource 两种结构"""
    db_config = nacos_data.get("db")
    if isinstance(db_config, dict) and db_config:
        return db_config

    datasource = nacos_data.get("spring", {}).get("datasource", {})
    if not isinstance(datasource, dict) or not datasource:
        return {}

    jdbc_url = datasource.get("url", "")
    match = re.match(
        r"^jdbc:mysql://(?P<host>[^:/?#]+)(?::(?P<port>\d+))?/(?P<database>[^?]+)",
        jdbc_url,
    )
    parsed = {}
    if match:
        parsed = {
            "host": match.group("host"),
            "port": int(match.group("port") or 3306),
            "database": match.group("database"),
        }

    if datasource.get("username"):
        parsed["username"] = datasource["username"]
    if datasource.get("password"):
        parsed["password"] = datasource["password"]
    return parsed


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

    augment_nacos = nacos_data.get("auto-augment-pipeline", {})
    auto_augment_pipeline = AutoAugmentPipelineConfig(
        base_url=os.getenv(
            "AUTO_AUGMENT_PIPELINE_URL",
            augment_nacos.get("base_url", "http://auto-augment-pipeline:8010"),
        ),
        timeout=int(os.getenv(
            "AUTO_AUGMENT_PIPELINE_TIMEOUT",
            augment_nacos.get("timeout", 120),
        )),
        default_profile=os.getenv(
            "AUTO_AUGMENT_PIPELINE_DEFAULT_PROFILE",
            augment_nacos.get("default_profile", "assist_default"),
        ),
    )

    return Settings(
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "45678")),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        database=database,
        nacos=nacos_config,
        model_trainer=model_trainer,
        model_deploy=model_deploy,
        auto_augment_pipeline=auto_augment_pipeline,
    )


def get_settings() -> Settings:
    """获取全局配置（单例）"""
    return _load_settings()
