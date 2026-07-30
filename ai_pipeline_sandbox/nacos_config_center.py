"""Nacos configuration synchronization for the batch sandbox."""
from __future__ import annotations

import asyncio
import os
import threading
from pathlib import Path
from typing import Callable

import yaml
from loguru import logger

ConfigCallback = Callable[[dict, dict], None]


class NacosConfigCenter:
    """Keep one cached Nacos configuration with listener and polling fallback."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._callbacks: dict[str, ConfigCallback] = {}
        self._config_text: str | None = None
        self._config_data: dict = {}
        self._poll_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._started = False
        self._last_fetch_failed = False
        self._listener_mode = "poll"
        self._listener_loop: asyncio.AbstractEventLoop | None = None
        self._listener_thread: threading.Thread | None = None
        self._listener_service = None

    @staticmethod
    def enabled() -> bool:
        return os.getenv("USE_NACOS", "true").lower() == "true"

    @staticmethod
    def poll_interval() -> int:
        return max(1, int(os.getenv("NACOS_CONFIG_POLL_INTERVAL", "5")))

    @staticmethod
    def _client_args() -> tuple[str, str, str, str]:
        return (
            os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848"),
            os.getenv("NACOS_NAMESPACE", "public"),
            os.getenv("NACOS_DATA_ID", "AUTO_ML_CONFIG"),
            os.getenv("NACOS_GROUP", "AUTO_ML"),
        )

    def register_callback(self, name: str, callback: ConfigCallback) -> None:
        with self._lock:
            self._callbacks[name] = callback

    def unregister_callback(self, name: str) -> None:
        with self._lock:
            self._callbacks.pop(name, None)

    def get_config_data(self) -> dict:
        if not self.enabled():
            return {}
        with self._lock:
            if self._config_text is not None:
                return self._config_data
        return self.refresh(notify=False)

    def refresh(self, notify: bool = True) -> dict:
        if not self.enabled():
            with self._lock:
                self._config_text = None
                self._config_data = {}
            return {}
        try:
            return self._apply_config_text(self._fetch_config_text(), notify=notify)
        except Exception as exc:
            if not self._last_fetch_failed:
                logger.warning("Failed to refresh Nacos config: {}", exc)
            self._last_fetch_failed = True
            with self._lock:
                return self._config_data

    def start(self) -> None:
        if not self.enabled() or self._started:
            return
        self.refresh(notify=False)
        self._stop_event.clear()
        if not self._start_listener():
            self._start_polling()
        self._started = True
        logger.info("Nacos config sync started: mode={}", self._listener_mode)

    def stop(self) -> None:
        if not self._started:
            return
        self._stop_event.set()
        self._stop_listener()
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=5)
        self._poll_thread = None
        self._started = False
        logger.info("Nacos config sync stopped")

    def _start_listener(self) -> bool:
        try:
            from v2.nacos import ClientConfigBuilder, ConfigParam, GRPCConfig, NacosConfigService
        except ImportError:
            logger.info("Nacos v2 listener unavailable; falling back to polling")
            return False

        server_addr, namespace, data_id, group = self._client_args()

        def run_listener() -> None:
            loop = asyncio.new_event_loop()
            self._listener_loop = loop
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self._listener_main(
                    ClientConfigBuilder,
                    GRPCConfig,
                    NacosConfigService,
                    ConfigParam,
                    server_addr,
                    namespace,
                    data_id,
                    group,
                )
            )

        self._listener_thread = threading.Thread(
            target=run_listener,
            name="pipeline-sandbox-nacos-listener",
            daemon=True,
        )
        self._listener_thread.start()
        self._listener_mode = "listener"
        return True

    async def _listener_main(
        self,
        ClientConfigBuilder,
        GRPCConfig,
        NacosConfigService,
        ConfigParam,
        server_addr: str,
        namespace: str,
        data_id: str,
        group: str,
    ) -> None:
        try:
            builder = (
                ClientConfigBuilder()
                .server_address(server_addr)
                .log_level("INFO")
                .grpc_config(GRPCConfig(grpc_timeout=5000))
            )
            if namespace:
                builder = builder.namespace_id(namespace)
            self._listener_service = await NacosConfigService.create_config_service(builder.build())
            param = ConfigParam(data_id=data_id, group=group)
            config_text = await self._listener_service.get_config(param)
            self._apply_config_text(config_text or "", notify=True)

            async def on_change(_tenant, changed_data_id, changed_group, content):
                logger.info(
                    "Nacos listener received update: data_id={} group={}",
                    changed_data_id,
                    changed_group,
                )
                self._apply_config_text(content or "", notify=True)

            await self._listener_service.add_listener(
                data_id=param.data_id,
                group=param.group,
                listener=on_change,
            )
            while not self._stop_event.is_set():
                await asyncio.sleep(1)
        except Exception as exc:
            logger.warning("Nacos listener failed; falling back to polling: {}", exc)
            self._listener_mode = "poll"
            self._start_polling()
        finally:
            if self._listener_service is not None:
                try:
                    await self._listener_service.shutdown()
                except Exception:
                    pass
                self._listener_service = None

    def _stop_listener(self) -> None:
        if self._listener_loop and self._listener_loop.is_running():
            self._listener_loop.call_soon_threadsafe(lambda: None)
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=5)
        self._listener_loop = None
        self._listener_thread = None

    def _start_polling(self) -> None:
        if self._poll_thread and self._poll_thread.is_alive():
            return
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            name="pipeline-sandbox-nacos-poller",
            daemon=True,
        )
        self._poll_thread.start()
        self._listener_mode = "poll"
        logger.info("Nacos config polling started: interval_seconds={}", self.poll_interval())

    def _poll_loop(self) -> None:
        while not self._stop_event.wait(self.poll_interval()):
            self.refresh(notify=True)

    def _fetch_config_text(self) -> str:
        import nacos

        server_addr, namespace, data_id, group = self._client_args()
        cache_root = Path(
            os.getenv("PIPELINE_SANDBOX_WORKSPACE", "/app/runtime-data")
        ) / "nacos"
        failover_base = cache_root / "data"
        snapshot_base = cache_root / "snapshot"
        failover_base.mkdir(parents=True, exist_ok=True)
        snapshot_base.mkdir(parents=True, exist_ok=True)
        client = nacos.NacosClient(
            server_addr,
            namespace=namespace,
            logDir=str(cache_root / "logs"),
        )
        client.set_options(
            failover_base=str(failover_base),
            snapshot_base=str(snapshot_base),
        )
        return client.get_config(data_id, group) or ""

    def _apply_config_text(self, config_text: str, notify: bool = True) -> dict:
        config_data = yaml.safe_load(config_text) or {}
        if not isinstance(config_data, dict):
            raise ValueError("Nacos configuration must be a YAML mapping")

        with self._lock:
            changed = config_text != self._config_text
            old_config = self._config_data
            self._config_text = config_text
            self._config_data = config_data
            callbacks = dict(self._callbacks)

        if self._last_fetch_failed:
            logger.info("Nacos config refresh recovered")
        self._last_fetch_failed = False

        if changed and notify:
            logger.info("Nacos config updated: keys={}", list(config_data.keys()))
            for name, callback in callbacks.items():
                try:
                    callback(old_config, config_data)
                except Exception as exc:
                    logger.opt(exception=True).error("Nacos config callback '{}' failed", name)
        return config_data


_config_center = NacosConfigCenter()


def get_config_center() -> NacosConfigCenter:
    return _config_center
