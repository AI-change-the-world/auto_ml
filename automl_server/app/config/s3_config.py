"""
S3/MinIO 配置
"""
import os
from functools import lru_cache
from typing import Optional

import yaml
from pydantic import BaseModel
from loguru import logger


class S3Config(BaseModel):
    """S3 配置"""
    access_key: str = ""
    secret_key: str = ""
    endpoint: str = "http://localhost:9000"
    region: str = "us-east-1"
    
    # 多 Bucket 配置
    default_bucket: str = "automl"
    datasets_bucket: str = "automl-datasets"
    models_bucket: str = "automl-models"
    annotations_bucket: str = "automl-annotations"
    augmented_bucket: str = "automl-augmented"
    
    # 预签名 URL 过期时间（秒）
    presigned_url_expires: int = 3600


def _load_s3_from_nacos() -> S3Config:
    """从 Nacos 加载 S3 配置"""
    try:
        import nacos
        
        nacos_addr = os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848")
        nacos_namespace = os.getenv("NACOS_NAMESPACE", "public")
        data_id = os.getenv("NACOS_DATA_ID", "AUTO_ML_CONFIG")
        group = os.getenv("NACOS_GROUP", "AUTO_ML")
        
        client = nacos.NacosClient(nacos_addr, namespace=nacos_namespace)
        config_str = client.get_config(data_id, group)
        config = yaml.safe_load(config_str) or {}
        
        s3 = config.get("local-s3-config", {})
        return S3Config(
            access_key=s3.get("access_key", ""),
            secret_key=s3.get("secret_key", ""),
            endpoint=s3.get("endpoint", "http://localhost:9000"),
            region=s3.get("region", "us-east-1"),
            default_bucket=s3.get("bucket_name", "automl"),
            datasets_bucket=s3.get("datasets_bucket_name", "automl-datasets"),
            models_bucket=s3.get("models_bucket_name", "automl-models"),
            annotations_bucket=s3.get("annotations_bucket_name", "automl-annotations"),
            augmented_bucket=s3.get("augmented_bucket_name", "automl-augmented"),
        )
    except Exception as e:
        logger.warning(f"Failed to load S3 config from Nacos: {e}")
        return _load_s3_from_env()


def _load_s3_from_env() -> S3Config:
    """从环境变量加载 S3 配置"""
    return S3Config(
        access_key=os.getenv("S3_ACCESS_KEY", ""),
        secret_key=os.getenv("S3_SECRET_KEY", ""),
        endpoint=os.getenv("S3_ENDPOINT", "http://localhost:9000"),
        region=os.getenv("S3_REGION", "us-east-1"),
        default_bucket=os.getenv("S3_DEFAULT_BUCKET", "automl"),
        datasets_bucket=os.getenv("S3_DATASETS_BUCKET", "automl-datasets"),
        models_bucket=os.getenv("S3_MODELS_BUCKET", "automl-models"),
        annotations_bucket=os.getenv("S3_ANNOTATIONS_BUCKET", "automl-annotations"),
        augmented_bucket=os.getenv("S3_AUGMENTED_BUCKET", "automl-augmented"),
    )


@lru_cache(maxsize=1)
def get_s3_config() -> S3Config:
    """获取 S3 配置"""
    use_nacos = os.getenv("USE_NACOS", "true").lower() == "true"
    if use_nacos:
        return _load_s3_from_nacos()
    return _load_s3_from_env()
