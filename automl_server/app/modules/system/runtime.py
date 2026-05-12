"""系统 capability 运行时状态"""
import asyncio
from datetime import datetime
from threading import RLock
from typing import Any, Optional

from app.config.nacos_config_center import get_config_center
from app.config.settings import CapabilityConfig, ModuleCapabilityConfig
from app.modules.task.stream import StreamEvent, get_task_stream_hub


def _to_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def build_capability_config(payload: dict[str, Any] | None) -> CapabilityConfig:
    payload = payload or {}
    return CapabilityConfig(
        dataset=ModuleCapabilityConfig(
            enabled=_to_bool(payload.get("dataset", {}).get("enabled"), True),
        ),
        annotation=ModuleCapabilityConfig(
            enabled=_to_bool(payload.get("annotation", {}).get("enabled"), True),
        ),
        training=ModuleCapabilityConfig(
            enabled=_to_bool(payload.get("training", {}).get("enabled"), True),
        ),
        deployment=ModuleCapabilityConfig(
            enabled=_to_bool(payload.get("deployment", {}).get("enabled"), True),
        ),
    )


class CapabilityRuntimeState:
    """维护 capability 运行时快照，并在 Nacos 更新后广播变更。"""

    def __init__(self):
        self._lock = RLock()
        self._config: CapabilityConfig = CapabilityConfig()
        self._version = 0
        self._updated_at: Optional[str] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def initialize(self):
        config_data = get_config_center().get_config_data()
        capability_payload = config_data.get("capability", {}) if isinstance(config_data, dict) else {}
        self._apply_from_payload(capability_payload, broadcast=False)

    def get_config(self) -> CapabilityConfig:
        with self._lock:
            return self._config.model_copy(deep=True)

    def get_meta(self) -> tuple[int, Optional[str]]:
        with self._lock:
            return self._version, self._updated_at

    def update_from_nacos(self, old_config: dict, new_config: dict):
        old_payload = (old_config or {}).get("capability", {})
        new_payload = (new_config or {}).get("capability", {})
        if old_payload == new_payload:
            return
        self._apply_from_payload(new_payload, broadcast=True)

    def _apply_from_payload(self, payload: dict[str, Any], broadcast: bool):
        next_config = build_capability_config(payload)
        next_dump = next_config.model_dump(mode="json")

        with self._lock:
            current_dump = self._config.model_dump(mode="json")
            if current_dump == next_dump:
                return
            self._config = next_config
            self._version += 1
            self._updated_at = datetime.utcnow().isoformat()
            version = self._version
            updated_at = self._updated_at

        if broadcast:
            self._broadcast_change(version, updated_at, next_dump)

    def _broadcast_change(self, version: int, updated_at: Optional[str], config_payload: dict[str, Any]):
        if self._loop is None or not self._loop.is_running():
            return

        asyncio.run_coroutine_threadsafe(
            self._publish_change(version, updated_at, config_payload),
            self._loop,
        )

    async def _publish_change(self, version: int, updated_at: Optional[str], config_payload: dict[str, Any]):
        await get_task_stream_hub().publish(
            StreamEvent(
                event="capability_changed",
                task_id=None,
                data={
                    "capability": {
                        "version": version,
                        "updated_at": updated_at,
                        "config": config_payload,
                    }
                },
            )
        )


_runtime_state: Optional[CapabilityRuntimeState] = None


def get_capability_runtime_state() -> CapabilityRuntimeState:
    global _runtime_state
    if _runtime_state is None:
        _runtime_state = CapabilityRuntimeState()
    return _runtime_state
