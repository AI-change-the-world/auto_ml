"""
配置管理
从 Nacos 或环境变量获取 S3 配置
"""
import os
from typing import Optional

import opendal
from pydantic import BaseModel

from utils.config_center import get_config_center
from utils.logger import logger


class S3Properties(BaseModel):
    """S3 配置"""
    access_key: str
    secret_key: str
    endpoint: str
    models_bucket_name: str


class DeployConfig(BaseModel):
    """部署服务配置"""
    runtime_base_port: int = 9001
    runtime_max_port: int = 9100
    model_cache_dir: str = "./models"


def load_s3_config_from_nacos() -> S3Properties:
    """从 Nacos 加载 S3 配置"""
    try:
        config = get_config_center().get_config_data()
        if not config:
            return load_s3_config_from_env()

        s3_config = config.get("local-s3-config", {})
        return S3Properties(
            access_key=s3_config.get("access_key", ""),
            secret_key=s3_config.get("secret_key", ""),
            endpoint=s3_config.get("endpoint", ""),
            models_bucket_name=s3_config.get("models_bucket_name", ""),
        )
    except Exception as e:
        logger.warning(f"Failed to load from Nacos, using env config: {e}")
        return load_s3_config_from_env()


def load_s3_config_from_env() -> S3Properties:
    """从环境变量加载 S3 配置"""
    return S3Properties(
        access_key=os.getenv("S3_ACCESS_KEY", ""),
        secret_key=os.getenv("S3_SECRET_KEY", ""),
        endpoint=os.getenv("S3_ENDPOINT", ""),
        models_bucket_name=os.getenv("S3_MODELS_BUCKET", ""),
    )


def load_deploy_config_from_nacos() -> DeployConfig:
    """从 Nacos 加载部署配置"""
    try:
        config = get_config_center().get_config_data()
        if not config:
            return load_deploy_config_from_env()

        deploy_config = config.get("model-deploy", {})
        return DeployConfig(
            runtime_base_port=deploy_config.get("runtime_base_port", 9001),
            runtime_max_port=deploy_config.get("runtime_max_port", 9100),
            model_cache_dir=deploy_config.get("model_cache_dir", "./models"),
        )
    except Exception as e:
        logger.warning(f"Failed to load deploy config from Nacos: {e}")
        return load_deploy_config_from_env()


def load_deploy_config_from_env() -> DeployConfig:
    """从环境变量加载部署配置"""
    config = DeployConfig(
        runtime_base_port=int(os.getenv("RUNTIME_BASE_PORT", "9001")),
        runtime_max_port=int(os.getenv("RUNTIME_MAX_PORT", "9100")),
        model_cache_dir=os.getenv("MODEL_CACHE_DIR", "./models"),
    )
    os.makedirs(config.model_cache_dir, exist_ok=True)
    return config


def get_s3_config() -> S3Properties:
    """获取 S3 配置（优先从 Nacos）"""
    use_nacos = os.getenv("USE_NACOS", "true").lower() == "true"
    if use_nacos:
        return load_s3_config_from_nacos()
    return load_s3_config_from_env()


def get_deploy_config() -> DeployConfig:
    """获取部署配置"""
    use_nacos = os.getenv("USE_NACOS", "true").lower() == "true"
    if use_nacos:
        return load_deploy_config_from_nacos()
    return load_deploy_config_from_env()


def get_s3_operator(bucket_name: Optional[str] = None) -> opendal.Operator:
    """获取 S3 操作器"""
    cfg = get_s3_config()
    b_n = bucket_name or cfg.models_bucket_name
    return opendal.Operator(
        "s3",
        endpoint=cfg.endpoint,
        access_key_id=cfg.access_key,
        secret_access_key=cfg.secret_key,
        region="us-east-1",
        bucket=b_n,
        root="/",
        enable_virtual_host_style="false",
    )


def download_from_s3(s3_path: str, local_path: str, bucket_name: Optional[str] = None):
    """从 S3 下载文件"""
    try:
        op = get_s3_operator(bucket_name)
        data = op.read(s3_path)
        with open(local_path, "wb") as f:
            f.write(data)
    except Exception as e:
        raise Exception(f"Error downloading from S3: {e}")
