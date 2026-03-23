import os
from functools import lru_cache
from typing import Optional

import opendal
from pydantic import BaseModel


class S3Properties(BaseModel):
    access_key: str
    secret_key: str
    bucket_name: str
    endpoint: str
    models_bucket_name: str


class DeployConfig(BaseModel):
    s3: S3Properties
    runtime_base_port: int = 9001
    runtime_max_port: int = 9100
    model_cache_dir: str = "./models"


def load_s3_config_from_env() -> S3Properties:
    """从环境变量加载 S3 配置"""
    return S3Properties(
        access_key=os.getenv("S3_ACCESS_KEY", ""),
        secret_key=os.getenv("S3_SECRET_KEY", ""),
        bucket_name=os.getenv("S3_BUCKET_NAME", ""),
        endpoint=os.getenv("S3_ENDPOINT", ""),
        models_bucket_name=os.getenv("S3_MODELS_BUCKET", ""),
    )


@lru_cache(maxsize=1)
def get_deploy_config() -> DeployConfig:
    """获取部署服务配置"""
    config = DeployConfig(
        s3=load_s3_config_from_env(),
        runtime_base_port=int(os.getenv("RUNTIME_BASE_PORT", "9001")),
        runtime_max_port=int(os.getenv("RUNTIME_MAX_PORT", "9100")),
        model_cache_dir=os.getenv("MODEL_CACHE_DIR", "./models"),
    )
    # 确保模型缓存目录存在
    os.makedirs(config.model_cache_dir, exist_ok=True)
    return config


@lru_cache(maxsize=10)
def get_s3_operator(bucket_name: Optional[str] = None) -> opendal.Operator:
    """获取 S3 操作器"""
    cfg = get_deploy_config().s3
    b_n = bucket_name or cfg.bucket_name
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
