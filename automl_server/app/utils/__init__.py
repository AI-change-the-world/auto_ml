"""工具类模块"""
from .s3_delegate import S3Delegate, get_s3_delegate
from .http_client import HttpClient, get_http_client

__all__ = [
    "S3Delegate", "get_s3_delegate",
    "HttpClient", "get_http_client",
]
