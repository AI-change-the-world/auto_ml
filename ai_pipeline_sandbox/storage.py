"""Private dataset object download for sandbox task workspaces."""
from __future__ import annotations

from pathlib import Path

import opendal

from config import StorageSettings


class DatasetStorage:
    def __init__(self, settings: StorageSettings) -> None:
        self._operator = opendal.AsyncOperator(
            "s3",
            endpoint=settings.endpoint,
            access_key_id=settings.access_key,
            secret_access_key=settings.secret_key,
            region=settings.region,
            bucket=settings.datasets_bucket,
            disable_ec2_metadata="true",
        )

    async def download(self, object_key: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = await self._operator.read(object_key)
        destination.write_bytes(bytes(data))
