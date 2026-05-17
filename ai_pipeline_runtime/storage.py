from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import opendal
import yaml


@dataclass
class S3Config:
    access_key: str
    secret_key: str
    endpoint: str
    annotations_bucket_name: str


def _fetch_nacos_payload() -> dict[str, Any]:
    server_addr = os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848")
    namespace = os.getenv("NACOS_NAMESPACE", "public")
    data_id = os.getenv("AUTO_ML_NACOS_DATA_ID", "AUTO_ML_CONFIG")
    group = os.getenv("NACOS_GROUP", "AUTO_ML")
    log_dir = os.getenv("STORAGE_NACOS_LOG_DIR", "/tmp/ai_pipeline_runtime/nacos/storage-logs")
    import nacos

    client = nacos.NacosClient(server_addr, namespace=namespace, logDir=log_dir)
    content = client.get_config(data_id, group) or ""
    payload = yaml.safe_load(content) or {}
    if not isinstance(payload, dict):
        raise RuntimeError("Nacos storage config payload must be a mapping")
    return payload


@lru_cache(maxsize=1)
def get_s3_config() -> S3Config:
    payload = _fetch_nacos_payload()
    s3 = payload.get("local-s3-config", {}) if isinstance(payload, dict) else {}
    if not isinstance(s3, dict):
        raise RuntimeError("local-s3-config is missing in Nacos config")
    return S3Config(
        access_key=str(s3.get("access_key", "")),
        secret_key=str(s3.get("secret_key", "")),
        endpoint=str(s3.get("endpoint", "")),
        annotations_bucket_name=str(s3.get("annotations_bucket_name", "")),
    )


def get_s3_operator(bucket_name: str | None = None) -> opendal.Operator:
    cfg = get_s3_config()
    bucket = bucket_name or cfg.annotations_bucket_name
    if not bucket:
        raise RuntimeError("annotations bucket is not configured")
    return opendal.Operator(
        "s3",
        endpoint=cfg.endpoint,
        access_key_id=cfg.access_key,
        secret_access_key=cfg.secret_key,
        region="us-east-1",
        bucket=bucket,
        root="/",
        enable_virtual_host_style="false",
        disable_ec2_metadata="true",
    )


def upload_bytes_to_s3(data: bytes, s3_path: str, bucket_name: str | None = None) -> str:
    op = get_s3_operator(bucket_name)
    op.write(s3_path, data)
    return s3_path
