"""
异步 HTTP 客户端
"""
from functools import lru_cache
from typing import Any, Dict, Optional

import httpx
from loguru import logger

from app.config.settings import get_settings


class HttpClient:
    """异步 HTTP 客户端"""

    def __init__(self, base_url: str = None, timeout: int = None):
        settings = get_settings()
        self.base_url = base_url or settings.ai_platform.base_url
        self.timeout = timeout or settings.ai_platform.timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=30.0),
            )
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def get(
        self,
        path: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> httpx.Response:
        """GET 请求"""
        client = await self._get_client()
        response = await client.get(path, params=params, headers=headers)
        return response

    async def post(
        self,
        path: str,
        data: Dict[str, Any] = None,
        json: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        files: Dict[str, Any] = None
    ) -> httpx.Response:
        """POST 请求"""
        client = await self._get_client()
        response = await client.post(
            path,
            data=data,
            json=json,
            headers=headers,
            files=files,
        )
        return response

    async def put(
        self,
        path: str,
        data: Dict[str, Any] = None,
        json: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> httpx.Response:
        """PUT 请求"""
        client = await self._get_client()
        response = await client.put(path, data=data, json=json, headers=headers)
        return response

    async def delete(
        self,
        path: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> httpx.Response:
        """DELETE 请求"""
        client = await self._get_client()
        response = await client.delete(path, params=params, headers=headers)
        return response

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            response = await self.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False


@lru_cache(maxsize=1)
def get_http_client() -> HttpClient:
    """获取 HTTP 客户端单例"""
    return HttpClient()
