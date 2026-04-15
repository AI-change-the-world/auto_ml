"""
S3/MinIO 操作封装 - 基于 OpenDAL
支持多 Bucket、预签名 URL 缓存
"""
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import opendal
from loguru import logger

from app.config.s3_config import get_s3_config, S3Config


class PresignedUrlCache:
    """预签名 URL 缓存"""

    def __init__(self, ttl_seconds: int = 3000):
        self._cache: Dict[str, tuple[str, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            url, expires = self._cache[key]
            if datetime.now() < expires:
                return url
            del self._cache[key]
        return None

    def set(self, key: str, url: str):
        self._cache[key] = (url, datetime.now() + self._ttl)

    def clear(self):
        self._cache.clear()


class S3Delegate:
    """S3/MinIO 操作委托类 - OpenDAL 实现"""

    def __init__(self, config: S3Config = None):
        self.config = config or get_s3_config()
        self._operators: Dict[str, opendal.AsyncOperator] = {}
        self._url_cache = PresignedUrlCache(
            self.config.presigned_url_expires - 600)

    def _get_operator(self, bucket_type: str = "default") -> opendal.AsyncOperator:
        """获取指定 bucket 的 AsyncOperator（带缓存）"""
        bucket = self.get_bucket_name(bucket_type)
        if bucket not in self._operators:
            kwargs = {
                "endpoint": self.config.endpoint,
                "access_key_id": self.config.access_key,
                "secret_access_key": self.config.secret_key,
                "region": self.config.region,
                "bucket": bucket,
                # 禁用 AWS 默认凭证链（EC2 元数据服务等），避免本地开发时访问 169.254.169.254
                "disable_ec2_metadata": "true",
            }
            self._operators[bucket] = opendal.AsyncOperator("s3", **kwargs)
        return self._operators[bucket]

    def get_bucket_name(self, bucket_type: str = "default") -> str:
        """根据类型获取 bucket 名称"""
        bucket_map = {
            "default": self.config.default_bucket,
            "datasets": self.config.datasets_bucket,
            "models": self.config.models_bucket,
            "annotations": self.config.annotations_bucket,
        }
        return bucket_map.get(bucket_type, self.config.default_bucket)

    async def ensure_buckets(self):
        """检查并创建所有需要的 bucket（使用 requests + S3 v4 签名）"""
        import requests as req

        all_buckets = [
            self.config.default_bucket,
            self.config.datasets_bucket,
            self.config.models_bucket,
            self.config.annotations_bucket,
        ]
        buckets = list(dict.fromkeys(all_buckets))  # 去重

        endpoint = self.config.endpoint.rstrip("/")
        parsed = urllib.parse.urlparse(endpoint)
        host = parsed.netloc
        scheme = parsed.scheme

        for bucket in buckets:
            try:
                # HEAD 检查 bucket 是否存在
                headers, url = self._sign_bucket_request(
                    "HEAD", bucket, host, scheme)
                resp = req.head(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    logger.info(f"Bucket '{bucket}' already exists")
                    continue
            except Exception:
                pass

            # 创建 bucket
            try:
                headers, url = self._sign_bucket_request(
                    "PUT", bucket, host, scheme)
                resp = req.put(url, headers=headers, data=b"", timeout=5)
                if resp.status_code in (200, 409):
                    logger.info(f"Bucket '{bucket}' ensured")
                else:
                    logger.warning(
                        f"Create bucket '{bucket}' failed: {resp.status_code}")
            except Exception as e:
                logger.warning(f"Create bucket '{bucket}' error: {e}")

    def _sign_bucket_request(
        self, method: str, bucket: str, host: str, scheme: str
    ) -> tuple[dict, str]:
        """为 bucket 操作生成 S3 v4 签名头"""
        now = datetime.utcnow()
        date_stamp = now.strftime("%Y%m%d")
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        region = self.config.region
        access_key = self.config.access_key
        secret_key = self.config.secret_key

        canonical_uri = f"/{bucket}"
        payload_hash = hashlib.sha256(b"").hexdigest()
        credential_scope = f"{date_stamp}/{region}/s3/aws4_request"

        canonical_headers = f"host:{host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n"
        signed_headers = "host;x-amz-content-sha256;x-amz-date"
        canonical_request = f"{method}\n{canonical_uri}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

        string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"

        def _sign(key_bytes: bytes, msg: str) -> bytes:
            return hmac.new(key_bytes, msg.encode(), hashlib.sha256).digest()

        signing_key = _sign(
            _sign(
                _sign(_sign(f"AWS4{secret_key}".encode(), date_stamp), region), "s3"),
            "aws4_request"
        )
        signature = hmac.new(
            signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

        authorization = (
            f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        headers = {
            "Host": host,
            "x-amz-date": amz_date,
            "x-amz-content-sha256": payload_hash,
            "Authorization": authorization,
        }
        url = f"{scheme}://{host}{canonical_uri}"
        return headers, url

    async def put_file(
        self,
        key: str,
        data: bytes,
        bucket_type: str = "default",
        content_type: str = None
    ):
        """上传文件"""
        op = self._get_operator(bucket_type)
        await op.write(key, data)
        logger.debug(f"Uploaded file to {bucket_type}:{key}")

    async def get_file(self, key: str, bucket_type: str = "default") -> bytes:
        """下载文件"""
        op = self._get_operator(bucket_type)
        data = await op.read(key)
        return bytes(data)

    async def delete_file(self, key: str, bucket_type: str = "default"):
        """删除文件"""
        op = self._get_operator(bucket_type)
        await op.delete(key)
        logger.debug(f"Deleted file {bucket_type}:{key}")

    async def list_files(
        self,
        prefix: str = "",
        bucket_type: str = "default",
        max_keys: int = 1000
    ) -> List[str]:
        """列出文件"""
        op = self._get_operator(bucket_type)
        entries = await op.list(prefix)
        files = []
        for entry in entries:
            if not entry.path.endswith("/"):
                files.append(entry.path)
            if len(files) >= max_keys:
                break
        return files

    async def file_exists(self, key: str, bucket_type: str = "default") -> bool:
        """检查文件是否存在"""
        op = self._get_operator(bucket_type)
        try:
            await op.stat(key)
            return True
        except Exception:
            return False

    async def create_directory(self, path: str, bucket_type: str = "default"):
        """创建目录（S3 不需要显式创建目录，上传文件时自动创建）"""
        # OpenDAL 不允许 write 以 / 结尾的路径
        # S3/MinIO 中目录是虚拟的，上传文件时会自动创建路径
        # 这里用 .keep 占位文件来确保目录存在
        if not path.endswith("/"):
            path = path + "/"
        keep_path = path + ".keep"
        await self.put_file(keep_path, b"", bucket_type)

    async def get_presigned_url(
        self,
        key: str,
        bucket_type: str = "default",
        expires: int = None,
        method: str = "get_object"
    ) -> str:
        """获取预签名 URL（手动生成 S3 v4 presigned URL）"""
        bucket = self.get_bucket_name(bucket_type)
        cache_key = f"{bucket}:{key}:{method}"

        cached = self._url_cache.get(cache_key)
        if cached:
            return cached

        expires = expires or self.config.presigned_url_expires
        url = self._generate_presigned_url(bucket, key, expires)
        self._url_cache.set(cache_key, url)
        return url

    def _generate_presigned_url(self, bucket: str, key: str, expires: int) -> str:
        """生成 S3 v4 预签名 URL"""
        endpoint = self.config.endpoint.rstrip("/")
        region = self.config.region
        access_key = self.config.access_key
        secret_key = self.config.secret_key

        # 解析 endpoint
        parsed = urllib.parse.urlparse(endpoint)
        host = parsed.netloc
        scheme = parsed.scheme

        now = datetime.utcnow()
        date_stamp = now.strftime("%Y%m%d")
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        credential_scope = f"{date_stamp}/{region}/s3/aws4_request"

        canonical_uri = f"/{bucket}/{urllib.parse.quote(key, safe='/')}"

        query_params = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": f"{access_key}/{credential_scope}",
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(expires),
            "X-Amz-SignedHeaders": "host",
        }
        canonical_querystring = "&".join(
            f"{k}={urllib.parse.quote(v, safe='')}" for k, v in sorted(query_params.items())
        )

        canonical_headers = f"host:{host}\n"
        canonical_request = f"GET\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\nhost\nUNSIGNED-PAYLOAD"

        string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"

        def _sign(key_bytes: bytes, msg: str) -> bytes:
            return hmac.new(key_bytes, msg.encode(), hashlib.sha256).digest()

        signing_key = _sign(
            _sign(
                _sign(
                    _sign(f"AWS4{secret_key}".encode(), date_stamp),
                    region
                ),
                "s3"
            ),
            "aws4_request"
        )
        signature = hmac.new(
            signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

        return f"{scheme}://{host}{canonical_uri}?{canonical_querystring}&X-Amz-Signature={signature}"

    async def copy_file(
        self,
        src_key: str,
        dst_key: str,
        src_bucket_type: str = "default",
        dst_bucket_type: str = "default"
    ):
        """复制文件（读取后写入）"""
        data = await self.get_file(src_key, src_bucket_type)
        await self.put_file(dst_key, data, dst_bucket_type)
        logger.debug(
            f"Copied {src_bucket_type}:{src_key} to {dst_bucket_type}:{dst_key}")


def get_s3_delegate() -> S3Delegate:
    """获取 S3 操作委托单例"""
    return S3Delegate()
