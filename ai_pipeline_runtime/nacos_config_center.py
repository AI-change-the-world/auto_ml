"""
Nacos 配置中心同步
优先使用 nacos-sdk-python v2 listener，失败时回退为轮询
"""
from __future__ import annotations

import asyncio
import os
import threading
from typing import Callable, Dict, Optional

import yaml

from logging import getLogger

logger = getLogger(__name__)

ConfigCallback = Callable[[dict, dict], None]


class NacosConfigCenter:
    """Nacos 配置中心"""

    def __init__(self):
        self._lock = threading.RLock()
        self._callbacks: Dict[str, ConfigCallback] = {}
        self._config_text: Optional[str] = None
        self._config_data: dict = {}
        self._poll_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._started = False
        self._last_fetch_failed = False
        self._listener_mode = "poll"
        self._listener_loop: Optional[asyncio.AbstractEventLoop] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._listener_service = None

    @staticmethod
    def enabled() -> bool:
        return os.getenv(
            "AI_PIPELINE_RUNTIME_WATCH_NACOS",
            os.getenv("AUTO_AUGMENT_WATCH_NACOS", "true"),
        ).lower() == "true"

    @staticmethod
    def poll_interval() -> int:
        return max(
            1,
            int(
                os.getenv(
                    "AI_PIPELINE_RUNTIME_NACOS_POLL_INTERVAL",
                    os.getenv("AUTO_AUGMENT_NACOS_POLL_INTERVAL", "5"),
                )
            ),
        )

    @staticmethod
    def _client_args() -> tuple[str, str, str, str]:
        return (
            os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848"),
            os.getenv(
                "AI_PIPELINE_RUNTIME_NACOS_NAMESPACE",
                os.getenv("AUTO_AUGMENT_NACOS_NAMESPACE", os.getenv("NACOS_NAMESPACE", "public")),
            ),
            os.getenv(
                "AI_PIPELINE_RUNTIME_NACOS_DATA_ID",
                os.getenv("AUTO_AUGMENT_NACOS_DATA_ID", "AI_PIPELINE_RUNTIME"),
            ),
            os.getenv("NACOS_GROUP", "AUTO_ML"),
        )

    def register_callback(self, name: str, callback: ConfigCallback):
        with self._lock:
            self._callbacks[name] = callback

    def unregister_callback(self, name: str):
        with self._lock:
            self._callbacks.pop(name, None)

    def get_config_data(self) -> dict:
        with self._lock:
            if self._config_text is not None:
                return self._config_data
        return self.refresh(notify=False)

    def refresh(self, notify: bool = True) -> dict:
        try:
            config_text = self._fetch_config_text()
            return self._apply_config_text(config_text, notify=notify)
        except Exception as e:
            if not self._last_fetch_failed:
                logger.warning("Failed to refresh Nacos config: %s", e)
            self._last_fetch_failed = True
            with self._lock:
                return self._config_data

    def start(self):
        if not self.enabled() or self._started:
            return

        self.refresh(notify=False)
        self._stop_event.clear()

        if not self._start_listener():
            self._start_polling()

        self._started = True
        logger.info("Nacos config sync started, mode=%s", self._listener_mode)

    def stop(self):
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
            from v2.nacos import (
                ClientConfigBuilder,
                ConfigParam,
                GRPCConfig,
                NacosConfigService,
            )
        except ImportError:
            logger.info("Nacos v2 listener unavailable, falling back to polling")
            return False

        server_addr, namespace, data_id, group = self._client_args()

        def _run_listener():
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
            target=_run_listener,
            name="ai-pipeline-runtime-nacos-config-listener",
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
    ):
        try:
            builder = (
                ClientConfigBuilder()
                .server_address(server_addr)
                .log_level("INFO")
                .grpc_config(GRPCConfig(grpc_timeout=5000))
            )
            if namespace:
                builder = builder.namespace_id(namespace)
            client_config = builder.build()
            self._listener_service = await NacosConfigService.create_config_service(
                client_config
            )
            param = ConfigParam(data_id=data_id, group=group)
            config_text = await self._listener_service.get_config(param)
            self._apply_config_text(config_text or "", notify=False)

            async def on_change(tenant, changed_data_id, changed_group, content):
                logger.info(
                    "Nacos listener received update: dataId=%s, group=%s",
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
        except Exception as e:
            logger.warning("Nacos listener failed, falling back to polling: %s", e)
            self._listener_mode = "poll"
            self._start_polling()
        finally:
            if self._listener_service is not None:
                try:
                    await self._listener_service.shutdown()
                except Exception:
                    pass
                self._listener_service = None

    def _stop_listener(self):
        if self._listener_loop and self._listener_loop.is_running():
            self._listener_loop.call_soon_threadsafe(lambda: None)
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=5)
        self._listener_loop = None
        self._listener_thread = None

    def _start_polling(self):
        if self._poll_thread and self._poll_thread.is_alive():
            return

        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            name="ai-pipeline-runtime-nacos-config-poller",
            daemon=True,
        )
        self._poll_thread.start()
        self._listener_mode = "poll"
        logger.info(
            "Nacos config polling started, interval=%ss",
            self.poll_interval(),
        )

    def _poll_loop(self):
        while not self._stop_event.wait(self.poll_interval()):
            self.refresh(notify=True)

    def _fetch_config_text(self) -> str:
        import nacos

        server_addr, namespace, data_id, group = self._client_args()
        client = nacos.NacosClient(server_addr, namespace=namespace)
        return client.get_config(data_id, group) or ""

    def _apply_config_text(self, config_text: str, notify: bool = True) -> dict:
        config_data = yaml.safe_load(config_text) or {}

        callbacks: Dict[str, ConfigCallback] = {}
        old_config: dict = {}
        changed = False
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
            logger.info("Nacos config updated, keys=%s", list(config_data.keys()))
            for name, callback in callbacks.items():
                try:
                    callback(old_config, config_data)
                except Exception as e:
                    logger.error("Nacos config callback '%s' failed: %s", name, e)
        return config_data


_config_center = NacosConfigCenter()


def get_config_center() -> NacosConfigCenter:
    return _config_center
