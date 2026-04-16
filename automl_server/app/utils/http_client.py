"""
异步 HTTP 客户端
"""
import asyncio
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from requests import Response
from loguru import logger

RETRYABLE_STATUS_CODES = {502, 503, 504}


class HttpClient:
    """异步 HTTP 客户端"""

    def __init__(self, base_url: str, timeout: int = 30):
        if not base_url:
            raise ValueError("HttpClient requires an explicit base_url")
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout

    def _build_url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def _sync_request(
        self,
        method: str,
        path: str,
        *,
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        json: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        files: Dict[str, Any] = None,
    ) -> Response:
        """在线程池中执行的同步请求。

        requests 在本机开发 + VPN 环境下比 httpx 更稳定；每次请求使用短生命周期
        Session，并关闭 trust_env，避免系统代理/VPN 影响内部服务互调。
        """
        request_headers = {"Connection": "close"}
        if headers:
            request_headers.update(headers)

        session = requests.Session()
        session.trust_env = False
        try:
            return session.request(
                method,
                self._build_url(path),
                params=params,
                data=data,
                json=json,
                headers=request_headers,
                files=files,
                timeout=(min(30, self.timeout), self.timeout),
            )
        finally:
            session.close()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        json: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        files: Dict[str, Any] = None,
    ) -> Response:
        """请求入口，遇到临时 5xx 或网络抖动时重试一次。"""
        last_error: Optional[Exception] = None

        for attempt in range(1, 3):
            try:
                response = await asyncio.to_thread(
                    self._sync_request,
                    method,
                    path,
                    params=params,
                    data=data,
                    json=json,
                    headers=headers,
                    files=files,
                )
                if response.status_code not in RETRYABLE_STATUS_CODES or attempt == 2:
                    return response

                logger.warning(
                    f"{method} {self.base_url}{path} returned {response.status_code}, "
                    f"retrying ({attempt}/2)"
                )
            except requests.RequestException as exc:
                last_error = exc
                if attempt == 2:
                    raise
                logger.warning(
                    f"{method} {self.base_url}{path} failed on attempt {attempt}/2: {exc}"
                )

            await asyncio.sleep(0.2)

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"{method} {self.base_url}{path} failed without response")

    async def close(self):
        """兼容旧接口。当前实现每次请求使用短生命周期 Session。"""
        return None

    async def get(
        self,
        path: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> Response:
        """GET 请求"""
        return await self._request(
            "GET",
            path,
            params=params,
            headers=headers,
        )

    async def post(
        self,
        path: str,
        data: Dict[str, Any] = None,
        json: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        files: Dict[str, Any] = None
    ) -> Response:
        """POST 请求"""
        return await self._request(
            "POST",
            path,
            data=data,
            json=json,
            headers=headers,
            files=files,
        )

    async def put(
        self,
        path: str,
        data: Dict[str, Any] = None,
        json: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> Response:
        """PUT 请求"""
        return await self._request(
            "PUT",
            path,
            data=data,
            json=json,
            headers=headers,
        )

    async def delete(
        self,
        path: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> Response:
        """DELETE 请求"""
        return await self._request(
            "DELETE",
            path,
            params=params,
            headers=headers,
        )

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            response = await self.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
