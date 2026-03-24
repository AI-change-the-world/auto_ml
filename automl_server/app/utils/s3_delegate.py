"""
S3/MinIO 操作封装
支持异步操作、多 Bucket、预签名 URL 缓存
"""
import io
from functools import lru_cache
from typing import AsyncGenerator, Dict, List, Optional
from datetime import datetime, timedelta

import aioboto3
from botocore.config import Config
from loguru import logger

from app.config.s3_config import get_s3_config, S3Config


class PresignedUrlCache:
    """预签名 URL 缓存"""
    
    def __init__(self, ttl_seconds: int = 3000):
        self._cache: Dict[str, tuple[str, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存的 URL"""
        if key in self._cache:
            url, expires = self._cache[key]
            if datetime.now() < expires:
                return url
            del self._cache[key]
        return None
    
    def set(self, key: str, url: str):
        """设置缓存"""
        self._cache[key] = (url, datetime.now() + self._ttl)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()


class S3Delegate:
    """S3/MinIO 操作委托类"""
    
    def __init__(self, config: S3Config = None):
        self.config = config or get_s3_config()
        self._session = aioboto3.Session()
        self._url_cache = PresignedUrlCache(self.config.presigned_url_expires - 600)
    
    def _get_client_config(self):
        """获取 boto3 配置"""
        return {
            "service_name": "s3",
            "endpoint_url": self.config.endpoint,
            "aws_access_key_id": self.config.access_key,
            "aws_secret_access_key": self.config.secret_key,
            "region_name": self.config.region,
            "config": Config(signature_version="s3v4"),
        }
    
    def get_bucket_name(self, bucket_type: str = "default") -> str:
        """根据类型获取 bucket 名称"""
        bucket_map = {
            "default": self.config.default_bucket,
            "datasets": self.config.datasets_bucket,
            "models": self.config.models_bucket,
            "annotations": self.config.annotations_bucket,
            "augmented": self.config.augmented_bucket,
        }
        return bucket_map.get(bucket_type, self.config.default_bucket)
    
    async def put_file(
        self,
        key: str,
        data: bytes,
        bucket_type: str = "default",
        content_type: str = None
    ):
        """上传文件"""
        bucket = self.get_bucket_name(bucket_type)
        async with self._session.client(**self._get_client_config()) as s3:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            await s3.put_object(Bucket=bucket, Key=key, Body=data, **extra_args)
            logger.debug(f"Uploaded file to s3://{bucket}/{key}")
    
    async def put_file_stream(
        self,
        key: str,
        stream: AsyncGenerator[bytes, None],
        bucket_type: str = "default",
        content_type: str = None
    ):
        """流式上传文件"""
        # 收集所有数据
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        await self.put_file(key, data, bucket_type, content_type)
    
    async def get_file(self, key: str, bucket_type: str = "default") -> bytes:
        """下载文件"""
        bucket = self.get_bucket_name(bucket_type)
        async with self._session.client(**self._get_client_config()) as s3:
            response = await s3.get_object(Bucket=bucket, Key=key)
            data = await response["Body"].read()
            return data
    
    async def delete_file(self, key: str, bucket_type: str = "default"):
        """删除文件"""
        bucket = self.get_bucket_name(bucket_type)
        async with self._session.client(**self._get_client_config()) as s3:
            await s3.delete_object(Bucket=bucket, Key=key)
            logger.debug(f"Deleted file s3://{bucket}/{key}")
    
    async def list_files(
        self,
        prefix: str = "",
        bucket_type: str = "default",
        max_keys: int = 1000
    ) -> List[str]:
        """列出文件"""
        bucket = self.get_bucket_name(bucket_type)
        files = []
        async with self._session.client(**self._get_client_config()) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            ):
                for obj in page.get("Contents", []):
                    files.append(obj["Key"])
        return files
    
    async def file_exists(self, key: str, bucket_type: str = "default") -> bool:
        """检查文件是否存在"""
        bucket = self.get_bucket_name(bucket_type)
        async with self._session.client(**self._get_client_config()) as s3:
            try:
                await s3.head_object(Bucket=bucket, Key=key)
                return True
            except Exception:
                return False
    
    async def create_directory(self, path: str, bucket_type: str = "default"):
        """创建目录（上传空对象）"""
        if not path.endswith("/"):
            path = path + "/"
        await self.put_file(path, b"", bucket_type)
    
    async def get_presigned_url(
        self,
        key: str,
        bucket_type: str = "default",
        expires: int = None,
        method: str = "get_object"
    ) -> str:
        """获取预签名 URL"""
        bucket = self.get_bucket_name(bucket_type)
        cache_key = f"{bucket}:{key}:{method}"
        
        # 检查缓存
        cached = self._url_cache.get(cache_key)
        if cached:
            return cached
        
        expires = expires or self.config.presigned_url_expires
        async with self._session.client(**self._get_client_config()) as s3:
            url = await s3.generate_presigned_url(
                method,
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires,
            )
            self._url_cache.set(cache_key, url)
            return url
    
    async def copy_file(
        self,
        src_key: str,
        dst_key: str,
        src_bucket_type: str = "default",
        dst_bucket_type: str = "default"
    ):
        """复制文件"""
        src_bucket = self.get_bucket_name(src_bucket_type)
        dst_bucket = self.get_bucket_name(dst_bucket_type)
        async with self._session.client(**self._get_client_config()) as s3:
            await s3.copy_object(
                CopySource={"Bucket": src_bucket, "Key": src_key},
                Bucket=dst_bucket,
                Key=dst_key,
            )
            logger.debug(f"Copied s3://{src_bucket}/{src_key} to s3://{dst_bucket}/{dst_key}")


@lru_cache(maxsize=1)
def get_s3_delegate() -> S3Delegate:
    """获取 S3 操作委托单例"""
    return S3Delegate()
