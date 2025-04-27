import os

import opendal

# TODO nacos 读取环境变量
access_key = os.environ.get("AWS_ACCESS_KEY_ID") or "QBYnE95cE6hkYgXideUE"
secret_key = (
    os.environ.get("AWS_SECRET_ACCESS_KEY")
    or "4VWw8OyPjkPhlGwHOdvadQwjFCozuQoIGHed4DG7"
)
bucket_name = os.environ.get("AWS_BUCKET_NAME") or "predict-data-bucket"
endpoint = os.environ.get("AWS_ENDPOINT") or "http://127.0.0.1:9000"


class FileDelegate:
    """file_type: 0: image, 1: text, 2: video, 3: audio, 4: other

    storage_type: 0: local, 1: s3, 2: wevdav
    """

    def __init__(
        self, file_type: int, storage_type: int, url: str, file_name: str
    ) -> None:
        self.file_type = file_type
        self.storage_type = storage_type
        self.url = url
        self.file_name = file_name

        self.__file_path = self.url + "/" + self.file_name

    def get_file(self) -> bytes:
        if self.storage_type == 0:
            return self._get_from_local()
        elif self.storage_type == 1:
            return self._get_from_s3()

    def _get_from_local(self) -> bytes:
        """从本地磁盘读取文件"""
        if not os.path.exists(self.__file_path):
            raise FileNotFoundError(f"Local file not found: {self.__file_path}")

        with open(self.__file_path, "rb") as f:
            data = f.read()
            return data

    def _get_from_s3(self) -> bytes:
        """从S3读取文件"""
        op = opendal.Operator(
            "s3",
            endpoint=endpoint,
            access_key_id=access_key,
            secret_access_key=secret_key,
            region="us-east-1",
            bucket=bucket_name,
            root="/",
            enable_virtual_host_style="false",  # <=== 要加上！！！
        )
        return op.read(self.file_name)
