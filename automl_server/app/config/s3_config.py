"""
S3/MinIO 配置
"""
import os

import yaml
from pydantic import BaseModel
from loguru import logger

from .nacos_config_center import get_config_center


class S3Config(BaseModel):
    """S3 配置"""
    access_key: str = "68GsKGa0TUEX9F75z4ql"  # for test
    secret_key: str = "OeMMqlWIBFNQpoXAkEwEnN4Xxx7qhcCyqrG9RNm2"  # for test
    endpoint: str = "http://localhost:9000"
    region: str = "us-east-1"

    # 多 Bucket 配置
    default_bucket: str = "automl"
    datasets_bucket: str = "automl-datasets"
    models_bucket: str = "automl-models"
    annotations_bucket: str = "automl-annotations"

    # 预签名 URL 过期时间（秒）
    presigned_url_expires: int = 3600


def _load_s3_from_nacos() -> S3Config:
    """从 Nacos 加载 S3 配置"""
    try:
        config = get_config_center().get_config_data()
        if not config:
            return _load_s3_from_env()

        s3 = config.get("local-s3-config", {})
        kwargs = {}
        nacos_mapping = {
            "access_key": "access_key",
            "secret_key": "secret_key",
            "endpoint": "endpoint",
            "region": "region",
            "bucket_name": "default_bucket",
            "datasets_bucket_name": "datasets_bucket",
            "models_bucket_name": "models_bucket",
            "annotations_bucket_name": "annotations_bucket",
        }
        for nacos_key, field_name in nacos_mapping.items():
            val = s3.get(nacos_key)
            if val:  # 只在非空时设置，否则用类默认值
                kwargs[field_name] = val
        return S3Config(**kwargs)
    except Exception as e:
        logger.warning(f"Failed to load S3 config from Nacos: {e}")
        return _load_s3_from_env()


def _load_s3_from_env() -> S3Config:
    """从环境变量加载 S3 配置，未设置的项使用类默认值"""
    kwargs = {}
    env_mapping = {
        "S3_ACCESS_KEY": "access_key",
        "S3_SECRET_KEY": "secret_key",
        "S3_ENDPOINT": "endpoint",
        "S3_REGION": "region",
        "S3_DEFAULT_BUCKET": "default_bucket",
        "S3_DATASETS_BUCKET": "datasets_bucket",
        "S3_MODELS_BUCKET": "models_bucket",
        "S3_ANNOTATIONS_BUCKET": "annotations_bucket",
    }
    for env_key, field_name in env_mapping.items():
        val = os.getenv(env_key)
        if val is not None:
            kwargs[field_name] = val
    return S3Config(**kwargs)


def get_s3_config() -> S3Config:
    """获取 S3 配置"""
    use_nacos = os.getenv("USE_NACOS", "true").lower() == "true"
    if use_nacos:
        return _load_s3_from_nacos()
    return _load_s3_from_env()
