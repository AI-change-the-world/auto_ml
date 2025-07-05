import os
from functools import lru_cache
from typing import Optional

import opendal
from pydantic import BaseModel

from base.nacos_config import load_nacos_config


class S3Properties(BaseModel):
    access_key: str
    secret_key: str
    bucket_name: str
    endpoint: str
    datasets_bucket_name: str
    models_bucket_name: str


def load_all_s3_configs(data_id="LOCAL_S3_CONFIG", group="AUTO_ML") -> S3Properties:
    nacos_config = load_nacos_config(data_id, group)
    cfg = nacos_config.get("local-s3-config")
    return S3Properties(
        access_key=cfg.get("access_key"),
        secret_key=cfg.get("secret_key"),
        bucket_name=cfg.get("bucket_name"),
        endpoint=cfg.get("endpoint"),
        datasets_bucket_name=cfg.get("datasets_bucket_name"),
        models_bucket_name=cfg.get("models_bucket_name"),
    )


s3_properties: S3Properties = load_all_s3_configs()


@lru_cache(maxsize=10)
def get_operator(bucket_name: Optional[str] = None) -> opendal.Operator:
    b_n = bucket_name or s3_properties.bucket_name
    return opendal.Operator(
        "s3",
        endpoint=s3_properties.endpoint,
        access_key_id=s3_properties.access_key,
        secret_access_key=s3_properties.secret_key,
        region="us-east-1",
        bucket=b_n,
        root="/",
        enable_virtual_host_style="false",
    )


def get_temp_operator(
    access_key, secret_key, bucket_name, endpoint
) -> opendal.Operator:
    return opendal.Operator(
        "s3",
        endpoint=endpoint,
        access_key_id=access_key,
        secret_access_key=secret_key,
        region="us-east-1",
        bucket=bucket_name,
        root="/",
        enable_virtual_host_style="false",
    )


class GetFileRequest(BaseModel):
    file_type: int  # 0: image, 1: text, 2: video, 3: audio, 4: other
    storage_type: int  # 0: local, 1: s3, 2: webdav
    url: str
    file_name: str


class FileDelegate:
    def __init__(self, bucket_type: str = None) -> None:
        properties = load_all_s3_configs()
        if bucket_type is None:
            bucket_type = properties.bucket_name
        assert bucket_type in [
            properties.bucket_name,
            properties.datasets_bucket_name,
            properties.models_bucket_name,
        ]
        self.bucket_type = bucket_type

    def put_file_to_s3(self, prefix: str, file_path: str, file_name: str):
        op = get_operator(self.bucket_type)
        with open(file_path, "rb") as f:
            data = f.read()
        op.write(prefix + "/" + file_name, data)

    def put_bytes_to_s3(self, prefix: str, file_content: bytes, file_name: str):
        op = get_operator(self.bucket_type)
        op.write(prefix + "/" + file_name, file_content)

    def get_file(self, req: GetFileRequest) -> Optional[bytes]:
        if req.storage_type == 0:
            return self._get_from_local(req)
        elif req.storage_type == 1:
            return self._get_from_s3(req)
        return None

    def _get_from_local(self, req: GetFileRequest) -> bytes:
        file_path = os.path.join(req.url, req.file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Local file not found: {file_path}")

        with open(file_path, "rb") as f:
            return f.read()

    def _get_from_s3(self, req: GetFileRequest) -> bytes:
        op = get_operator(self.bucket_type)
        return op.read(req.file_name)
