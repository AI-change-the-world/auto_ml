import os
from typing import Optional

import opendal
from pydantic import BaseModel

from base.nacos_config import load_nacos_config


def get_op(data_id="LOCAL_S3_CONFIG", group="AUTO_ML") -> opendal.Operator:
    nacos_config = load_nacos_config(data_id, group)
    cfg = nacos_config.get("local-s3-config")
    return opendal.Operator(
        "s3",
        endpoint=cfg.get("endpoint"),
        access_key_id=cfg.get("access_key"),
        secret_access_key=cfg.get("secret_key"),
        region="us-east-1",
        bucket=cfg.get("bucket_name"),
        root="/",
        enable_virtual_host_style="false",  # <=== 要加上！！！
    )


class GetFileRequest(BaseModel):
    """file_type: 0: image, 1: text, 2: video, 3: audio, 4: other

    storage_type: 0: local, 1: s3, 2: wevdav
    """

    file_type: int
    storage_type: int
    url: str
    file_name: str


class FileDelegate:

    def __init__(self) -> None:
        pass

    def get_file(self, req: GetFileRequest) -> Optional[bytes]:
        if req.storage_type == 0:
            return self._get_from_local(req)
        elif req.storage_type == 1:
            return self._get_from_s3(req)
        return None

    def _get_from_local(self, req: GetFileRequest) -> bytes:
        """从本地磁盘读取文件"""
        __file_path = req.url + "/" + self.file_name
        if not os.path.exists(__file_path):
            raise FileNotFoundError(f"Local file not found: {__file_path}")

        with open(__file_path, "rb") as f:
            data = f.read()
            return data

    def _get_from_s3(self, req: GetFileRequest) -> bytes:
        """从S3读取文件"""
        op = get_op()
        return op.read(req.file_name)
