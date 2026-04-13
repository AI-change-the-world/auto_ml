"""
全局配置管理
优先从 Nacos 获取，回退到环境变量
"""
import os
from functools import lru_cache
from typing import Optional

import yaml
from pydantic import BaseModel
from loguru import logger


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


class AIPlatformConfig(BaseModel):
    """AI Platform 服务配置"""
    base_url: str = "http://localhost:45679"
    timeout: int = 1800


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
    ai_platform: AIPlatformConfig = AIPlatformConfig()

    # 心跳检查间隔（秒）
    heartbeat_interval: int = 300


def _load_from_nacos(nacos_config: NacosConfig) -> dict:
    """从 Nacos 加载配置"""
    try:
        import nacos

        client = nacos.NacosClient(
            nacos_config.server_addr,
            namespace=nacos_config.namespace
        )
        config_str = client.get_config(
            nacos_config.data_id, nacos_config.group)
        if config_str:
            return yaml.safe_load(config_str) or {}
        return {}
    except Exception as e:
        logger.warning(f"Failed to load config from Nacos: {e}")
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
        logger.info(f"Loaded config from Nacos: {list(nacos_data.keys())}")

    # 3. 合并配置：环境变量 > Nacos > DatabaseConfig 默认值
    _db_defaults = DatabaseConfig()
    db_nacos = nacos_data.get("db", {})
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

    ai_nacos = nacos_data.get("ai-platform", {})
    ai_platform = AIPlatformConfig(
        base_url=os.getenv("AI_PLATFORM_URL", ai_nacos.get(
            "base_url", "http://localhost:45679")),
        timeout=int(os.getenv("AI_PLATFORM_TIMEOUT",
                    ai_nacos.get("timeout", 1800))),
    )

    return Settings(
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "45678")),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        database=database,
        nacos=nacos_config,
        ai_platform=ai_platform,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取全局配置（单例）"""
    return _load_settings()
