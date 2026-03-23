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
    datasets_bucket_name: str
    models_bucket_name: str


class NacosConfig(BaseModel):
    server_addr: str = "127.0.0.1:8848"
    namespace: str = "public"
    data_id: str = "MODEL_TRAINER_CONFIG"
    group: str = "AUTO_ML"


class TrainerConfig(BaseModel):
    s3: S3Properties
    nacos: NacosConfig
    mq_type: str = "redis"  # redis / rabbitmq
    mq_url: str = "redis://localhost:6379/0"


def load_s3_config_from_env() -> S3Properties:
    """从环境变量加载 S3 配置"""
    return S3Properties(
        access_key=os.getenv("S3_ACCESS_KEY", ""),
        secret_key=os.getenv("S3_SECRET_KEY", ""),
        bucket_name=os.getenv("S3_BUCKET_NAME", ""),
        endpoint=os.getenv("S3_ENDPOINT", ""),
        datasets_bucket_name=os.getenv("S3_DATASETS_BUCKET", ""),
        models_bucket_name=os.getenv("S3_MODELS_BUCKET", ""),
    )


def load_nacos_config_from_env() -> NacosConfig:
    """从环境变量加载 Nacos 配置"""
    return NacosConfig(
        server_addr=os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848"),
        namespace=os.getenv("NACOS_NAMESPACE", "public"),
        data_id=os.getenv("NACOS_DATA_ID", "MODEL_TRAINER_CONFIG"),
        group=os.getenv("NACOS_GROUP", "AUTO_ML"),
    )


@lru_cache(maxsize=1)
def get_trainer_config() -> TrainerConfig:
    """获取训练服务配置"""
    return TrainerConfig(
        s3=load_s3_config_from_env(),
        nacos=load_nacos_config_from_env(),
        mq_type=os.getenv("MQ_TYPE", "redis"),
        mq_url=os.getenv("MQ_URL", "redis://localhost:6379/0"),
    )


@lru_cache(maxsize=10)
def get_s3_operator(bucket_name: Optional[str] = None) -> opendal.Operator:
    """获取 S3 操作器"""
    cfg = get_trainer_config().s3
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
