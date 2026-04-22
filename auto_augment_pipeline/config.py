from __future__ import annotations

import inspect
import logging
import os
import re
from pathlib import Path
from typing import Any, Awaitable, Callable

import yaml
from pydantic import BaseModel, Field

from models import PipelineDefinition

logger = logging.getLogger(__name__)

ConfigChangedCallback = Callable[["RuntimeConfig"], Any | Awaitable[Any]]


class ProviderConfig(BaseModel):
    kind: str = "openai_compatible"
    role: str = "multimodal"
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    timeout_seconds: float = 60.0
    temperature: float = 0.0
    max_tokens: int = 1024
    extra_headers: dict[str, str] = Field(default_factory=dict)
    extra: dict[str, Any] = Field(default_factory=dict)


class RuntimeConfig(BaseModel):
    service_name: str = "auto-augment-pipeline"
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    pipelines: dict[str, PipelineDefinition] = Field(default_factory=dict)


def _expand_env_vars(raw: str) -> str:
    pattern = re.compile(r"\$\{([A-Z0-9_]+)\}")

    def replace(match: re.Match[str]) -> str:
        return os.getenv(match.group(1), "")

    return pattern.sub(replace, raw)


class ConfigManager:
    def __init__(
        self,
        *,
        nacos_server_addr: str = "127.0.0.1:8848",
        nacos_namespace: str = "public",
        nacos_data_id: str = "AUTO_AUGMENT_PIPELINE",
        nacos_group: str = "AUTO_ML",
        nacos_log_dir: str | None = None,
        nacos_cache_dir: str | None = None,
        watch_nacos: bool = False,
    ) -> None:
        self.nacos_server_addr = nacos_server_addr
        self.nacos_namespace = nacos_namespace
        self.nacos_data_id = nacos_data_id
        self.nacos_group = nacos_group
        self.nacos_log_dir = nacos_log_dir
        self.nacos_cache_dir = nacos_cache_dir
        self.watch_nacos = watch_nacos
        self.current = RuntimeConfig()
        self._nacos_service: Any | None = None

    async def load(self) -> RuntimeConfig:
        raw = await self._load_from_nacos()
        if not raw:
            raise RuntimeError(
                f"Nacos config is empty: dataId={self.nacos_data_id}, group={self.nacos_group}, namespace={self.nacos_namespace}"
            )
        self.current = self._parse(raw)
        return self.current

    async def start_watch(self, on_change: ConfigChangedCallback | None = None) -> None:
        if not self.watch_nacos:
            return

        service = await self._ensure_nacos_service()

        async def listener(tenant: str, data_id: str, group: str, content: str) -> None:
            logger.info(
                "Detected config change from Nacos: dataId=%s group=%s", data_id, group)
            config = self._parse(content)
            self.current = config
            if on_change is None:
                return
            maybe_awaitable = on_change(config)
            if inspect.isawaitable(maybe_awaitable):
                await maybe_awaitable

        await service.add_listener(
            data_id=self.nacos_data_id,
            group=self.nacos_group,
            listener=listener,
        )

    async def close(self) -> None:
        if self._nacos_service is not None:
            await self._nacos_service.shutdown()
            self._nacos_service = None

    def _parse(self, raw: str) -> RuntimeConfig:
        expanded = _expand_env_vars(raw)
        data = yaml.safe_load(expanded) or {}
        if not data:
            raise RuntimeError("Nacos config payload is empty")
        return RuntimeConfig.model_validate(data)

    async def _load_from_nacos(self) -> str | None:
        try:
            from v2.nacos import ConfigParam
        except ImportError:
            raise RuntimeError(
                "nacos-sdk-python v2 is not installed") from None

        service = await self._ensure_nacos_service()
        return await service.get_config(
            ConfigParam(data_id=self.nacos_data_id, group=self.nacos_group)
        )

    async def _ensure_nacos_service(self) -> Any | None:
        if self._nacos_service is not None:
            return self._nacos_service

        try:
            from v2.nacos import ClientConfigBuilder, GRPCConfig, NacosConfigService
        except ImportError:
            raise RuntimeError(
                "nacos-sdk-python v2 is not installed") from None

        try:
            client_config = (
                ClientConfigBuilder()
                .server_address(self.nacos_server_addr)
                .namespace_id(self.nacos_namespace)
                .log_level("INFO")
                .log_dir(self.nacos_log_dir or str(Path("/tmp/auto_augment_pipeline/nacos/logs")))
                .cache_dir(self.nacos_cache_dir or str(Path("/tmp/auto_augment_pipeline/nacos/cache")))
                .grpc_config(GRPCConfig(grpc_timeout=5000))
                .build()
            )
            self._nacos_service = await NacosConfigService.create_config_service(client_config)
            return self._nacos_service
        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialize Nacos config service: {exc}") from exc


def create_config_manager_from_env() -> ConfigManager:
    watch_nacos = os.getenv("AUTO_AUGMENT_WATCH_NACOS", "true").strip().lower() in {
        "1", "true", "yes", "on"}
    return ConfigManager(
        nacos_server_addr=os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848"),
        nacos_namespace=os.getenv(
            "AUTO_AUGMENT_NACOS_NAMESPACE", os.getenv("NACOS_NAMESPACE", "public")),
        nacos_data_id=os.getenv(
            "AUTO_AUGMENT_NACOS_DATA_ID", "AUTO_AUGMENT_PIPELINE"),
        nacos_group=os.getenv("NACOS_GROUP", "AUTO_ML"),
        nacos_log_dir=os.getenv("AUTO_AUGMENT_NACOS_LOG_DIR"),
        nacos_cache_dir=os.getenv("AUTO_AUGMENT_NACOS_CACHE_DIR"),
        watch_nacos=watch_nacos,
    )
