"""
配置管理
从 Nacos 或环境变量获取 S3 配置
"""
import os
from functools import lru_cache
from typing import Optional

import opendal
import yaml
from pydantic import BaseModel

from utils.logger import logger


class S3Properties(BaseModel):
    """S3 配置"""
    access_key: str
    secret_key: str
    endpoint: str
    datasets_bucket_name: str
    models_bucket_name: str


def load_s3_config_from_nacos() -> S3Properties:
    """从 Nacos 加载 S3 配置"""
    try:
        import nacos

        nacos_addr = os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848")
        nacos_namespace = os.getenv("NACOS_NAMESPACE", "public")
        data_id = os.getenv("NACOS_DATA_ID", "AUTO_ML_CONFIG")
        group = os.getenv("NACOS_GROUP", "AUTO_ML")

        logger.info(
            f"Loading S3 config from Nacos: {nacos_addr}, {data_id}, {group}")

        client = nacos.NacosClient(nacos_addr, namespace=nacos_namespace)
        config_str = client.get_config(data_id, group)
        config = yaml.safe_load(config_str) or {}

        s3_config = config.get("local-s3-config", {})
        return S3Properties(
            access_key=s3_config.get("access_key", ""),
            secret_key=s3_config.get("secret_key", ""),
            endpoint=s3_config.get("endpoint", ""),
            datasets_bucket_name=s3_config.get("datasets_bucket_name", ""),
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
        datasets_bucket_name=os.getenv("S3_DATASETS_BUCKET", ""),
        models_bucket_name=os.getenv("S3_MODELS_BUCKET", ""),
    )


@lru_cache(maxsize=1)
def get_s3_config() -> S3Properties:
    """获取 S3 配置（优先从 Nacos）"""
    use_nacos = os.getenv("USE_NACOS", "true").lower() == "true"
    if use_nacos:
        return load_s3_config_from_nacos()
    return load_s3_config_from_env()


@lru_cache(maxsize=10)
def get_s3_operator(bucket_name: Optional[str] = None) -> opendal.Operator:
    """获取 S3 操作器"""
    cfg = get_s3_config()
    b_n = bucket_name or cfg.datasets_bucket_name
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


def upload_to_s3(local_path: str, s3_path: str, bucket_name: Optional[str] = None):
    """上传文件到 S3"""
    try:
        op = get_s3_operator(bucket_name)
        with open(local_path, "rb") as f:
            op.write(s3_path, f.read())
    except Exception as e:
        raise Exception(f"Error uploading to S3: {e}")
