"""Thin HTTP boundary for experimental immutable dataset snapshot registration."""
from __future__ import annotations

from typing import Any

from app.common.exceptions import BadRequestException
from app.utils.http_client import HttpClient

from .schemas import (
    TrainingDatasetSnapshotManifest,
    TrainingDatasetSnapshotRegistrationResponse,
)


class TrainingDatasetSnapshotRegistrar:
    """Calls the runtime only after the control plane has resolved a manifest."""

    def __init__(self, *, base_url: str, timeout: int, token: str = "") -> None:
        if not base_url.strip():
            raise BadRequestException("training code runtime URL is not configured")
        self._client = HttpClient(base_url=base_url, timeout=timeout)
        self._token = token.strip()

    async def register(
        self,
        manifest: TrainingDatasetSnapshotManifest,
        *,
        source_count: int,
    ) -> TrainingDatasetSnapshotRegistrationResponse:
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else None
        try:
            response = await self._client.post(
                "/v1/registrations/dataset-snapshots",
                json=manifest.model_dump(mode="json", exclude_none=True),
                headers=headers,
            )
        except Exception as exc:
            raise BadRequestException(
                f"training code runtime dataset snapshot registration failed: {exc}"
            ) from exc

        if response.status_code != 200:
            raise BadRequestException(
                "training code runtime dataset snapshot registration was rejected: "
                f"{response.status_code} {_response_detail(response)}"
            )

        try:
            payload = response.json()
            registration = payload["registration"]
            result = TrainingDatasetSnapshotRegistrationResponse(
                created=payload["created"],
                manifest=registration["source_manifest"],
                object=registration["object"],
                source_count=source_count,
                sample_count=len(registration["source_manifest"]["items"]),
            )
            _validate_registered_snapshot(manifest, result)
            return result
        except (KeyError, TypeError, ValueError) as exc:
            raise BadRequestException(
                "training code runtime returned an invalid dataset snapshot registration response"
            ) from exc


def _response_detail(response: Any) -> str:
    """Retain a small useful remote error without reflecting a large body to callers."""
    try:
        payload = response.json()
    except Exception:
        return ""
    if isinstance(payload, dict):
        detail = str(payload.get("detail") or payload.get("message") or "").strip()
        return detail[:500]
    return ""


def _validate_registered_snapshot(
    submitted: TrainingDatasetSnapshotManifest,
    registered: TrainingDatasetSnapshotRegistrationResponse,
) -> None:
    """Allow pinning only; a runtime must not alter control-plane source selection."""
    submitted_payload = submitted.model_dump(mode="json", exclude_none=True)
    registered_payload = registered.manifest.model_dump(mode="json", exclude_none=True)
    for field in ("protocol_version", "task_kind", "data_modalities", "annotation_kinds", "class_names"):
        if registered_payload[field] != submitted_payload[field]:
            raise ValueError(f"registered snapshot changed `{field}`")

    submitted_items = submitted_payload["items"]
    registered_items = registered_payload["items"]
    if len(registered_items) != len(submitted_items):
        raise ValueError("registered snapshot changed item count")
    for submitted_item, registered_item in zip(submitted_items, registered_items):
        for field in ("item_id", "split", "metadata"):
            if registered_item[field] != submitted_item[field]:
                raise ValueError(f"registered snapshot changed item `{field}`")
        _validate_pinned_reference(submitted_item["media"], registered_item["media"])
        _validate_pinned_reference(submitted_item["annotation"], registered_item["annotation"])

    snapshot = registered.object
    expected_object_key = f"training-code-runtime/dataset-snapshots/{snapshot.sha256}.json"
    if snapshot.object_key != expected_object_key:
        raise ValueError("registered snapshot object key does not match its SHA-256")


def _validate_pinned_reference(submitted: dict[str, Any], registered: dict[str, Any]) -> None:
    for field in ("bucket", "object_key"):
        if registered[field] != submitted[field]:
            raise ValueError(f"registered snapshot changed object `{field}`")
    if not registered.get("sha256") or registered.get("size_bytes") is None:
        raise ValueError("registered snapshot did not pin object SHA-256 and size_bytes")
