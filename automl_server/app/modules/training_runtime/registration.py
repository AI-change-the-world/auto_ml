"""HTTP boundary for immutable custom-training package registration."""
from __future__ import annotations

from typing import Any

from app.common.exceptions import BadRequestException
from app.utils.http_client import HttpClient

from .schemas import (
    RuntimeCodePackageRegistrationResult,
    RuntimeModelPackageRegistrationResult,
)


class TrainingRuntimeRegistrar:
    """Registers ZIP releases without scheduling or executing training work."""

    MAX_ARCHIVE_BYTES = 512 * 1024 * 1024

    def __init__(self, *, base_url: str, timeout: int, token: str = "") -> None:
        if not base_url.strip():
            raise BadRequestException("model training runtime URL is not configured")
        self._client = HttpClient(base_url=base_url, timeout=timeout)
        self._token = token.strip()

    async def register_code_package(
        self,
        *,
        archive_name: str,
        archive_bytes: bytes,
    ) -> RuntimeCodePackageRegistrationResult:
        payload = await self._register(
            path="/v1/registrations/packages",
            archive_name=archive_name,
            archive_bytes=archive_bytes,
            package_kind="training code package",
        )
        try:
            return RuntimeCodePackageRegistrationResult.model_validate(payload)
        except (TypeError, ValueError) as exc:
            raise BadRequestException(
                "training runtime returned an invalid code package registration response"
            ) from exc

    async def register_model_package(
        self,
        *,
        archive_name: str,
        archive_bytes: bytes,
    ) -> RuntimeModelPackageRegistrationResult:
        payload = await self._register(
            path="/v1/registrations/model-packages",
            archive_name=archive_name,
            archive_bytes=archive_bytes,
            package_kind="training model package",
        )
        try:
            return RuntimeModelPackageRegistrationResult.model_validate(payload)
        except (TypeError, ValueError) as exc:
            raise BadRequestException(
                "training runtime returned an invalid model package registration response"
            ) from exc

    async def _register(
        self,
        *,
        path: str,
        archive_name: str,
        archive_bytes: bytes,
        package_kind: str,
    ) -> dict[str, Any]:
        if not archive_name.lower().endswith(".zip"):
            raise BadRequestException(f"{package_kind} must be a .zip file")
        if not archive_bytes:
            raise BadRequestException(f"{package_kind} is empty")
        if len(archive_bytes) > self.MAX_ARCHIVE_BYTES:
            raise BadRequestException(f"{package_kind} exceeds the 512 MiB import limit")

        headers = {"Content-Type": "application/zip"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            response = await self._client.post(
                path,
                data=archive_bytes,
                params={"archive_name": archive_name},
                headers=headers,
            )
        except Exception as exc:
            raise BadRequestException(f"{package_kind} registration failed: {exc}") from exc

        if response.status_code != 200:
            raise BadRequestException(
                f"{package_kind} registration was rejected: "
                f"{response.status_code} {_response_detail(response)}"
            )
        payload = response.json()
        if not isinstance(payload, dict):
            raise BadRequestException(f"training runtime returned an invalid {package_kind} response")
        return payload


def _response_detail(response: Any) -> str:
    try:
        payload = response.json()
    except Exception:
        return ""
    if isinstance(payload, dict):
        detail = str(payload.get("detail") or payload.get("message") or "").strip()
        return detail[:500]
    return ""
