"""Private dataset object download for sandbox task workspaces."""
from __future__ import annotations

from pathlib import Path

import opendal

from config import StorageSettings


class DatasetStorage:
    def __init__(self, settings: StorageSettings) -> None:
        settings_kwargs = {
            "endpoint": settings.endpoint,
            "access_key_id": settings.access_key,
            "secret_access_key": settings.secret_key,
            "region": settings.region,
            "disable_ec2_metadata": "true",
        }
        self._dataset_operator = opendal.AsyncOperator(
            "s3",
            bucket=settings.datasets_bucket,
            **settings_kwargs,
        )
        self._script_operator = opendal.AsyncOperator(
            "s3",
            bucket=settings.default_bucket,
            **settings_kwargs,
        )

    async def download(self, object_key: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = await self._dataset_operator.read(object_key)
        destination.write_bytes(bytes(data))

    async def download_script_package(self, object_key: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = await self._script_operator.read(object_key)
        destination.write_bytes(bytes(data))
