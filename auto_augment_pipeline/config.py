from __future__ import annotations

import inspect
import logging
import os
import re
from pathlib import Path
from typing import Any, Awaitable, Callable

import yaml
from pydantic import BaseModel, Field

from .models import PipelineDefinition

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


class DefaultsConfig(BaseModel):
    multimodal_provider: str | None = None
    text_provider: str | None = None
    ocr_provider: str | None = None
    image_edit_provider: str | None = None


class ProfileConfig(BaseModel):
    multimodal_provider: str | None = None
    text_provider: str | None = None
    ocr_provider: str | None = None
    image_edit_provider: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class RuntimeConfig(BaseModel):
    service_name: str = "auto-augment-pipeline"
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    profiles: dict[str, ProfileConfig] = Field(default_factory=dict)
    pipelines: dict[str, PipelineDefinition] = Field(default_factory=dict)


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _expand_env_vars(raw: str) -> str:
    pattern = re.compile(r"\$\{([A-Z0-9_]+)\}")

    def replace(match: re.Match[str]) -> str:
        return os.getenv(match.group(1), "")

    return pattern.sub(replace, raw)


def build_default_config() -> RuntimeConfig:
    return RuntimeConfig(
        providers={
            "mock_vision": ProviderConfig(
                kind="mock",
                role="multimodal",
                model="mock-vision",
            )
        },
        defaults=DefaultsConfig(
            multimodal_provider="mock_vision",
            image_edit_provider="mock_vision",
        ),
    )


class ConfigManager:
    def __init__(
        self,
        *,
        config_path: str | None = None,
        use_nacos: bool = False,
        nacos_server_addr: str = "127.0.0.1:8848",
        nacos_data_id: str = "AUTO_AUGMENT_PIPELINE",
        nacos_group: str = "DEFAULT_GROUP",
        watch_nacos: bool = False,
    ) -> None:
        self.config_path = config_path
        self.use_nacos = use_nacos
        self.nacos_server_addr = nacos_server_addr
        self.nacos_data_id = nacos_data_id
        self.nacos_group = nacos_group
        self.watch_nacos = watch_nacos
        self.current = build_default_config()
        self._nacos_service: Any | None = None

    async def load(self) -> RuntimeConfig:
        if self.use_nacos:
            raw = await self._load_from_nacos()
            if raw:
                self.current = self._parse(raw)
                return self.current
            logger.warning("Nacos config is empty, falling back to local/default config")

        if self.config_path:
            path = Path(self.config_path).expanduser()
            if path.exists():
                self.current = self._parse(path.read_text(encoding="utf-8"))
                return self.current
            logger.warning("Config file not found: %s, using default config", path)

        self.current = build_default_config()
        return self.current

    async def start_watch(self, on_change: ConfigChangedCallback | None = None) -> None:
        if not self.use_nacos or not self.watch_nacos:
            return

        service = await self._ensure_nacos_service()
        if service is None:
            return

        async def listener(tenant: str, data_id: str, group: str, content: str) -> None:
            logger.info("Detected config change from Nacos: dataId=%s group=%s", data_id, group)
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
            return build_default_config()
        return RuntimeConfig.model_validate(data)

    async def _load_from_nacos(self) -> str | None:
        try:
            from v2.nacos import ConfigParam
        except ImportError:
            logger.warning("nacos-sdk-python v2 is not installed; skip loading Nacos config")
            return None

        service = await self._ensure_nacos_service()
        if service is None:
            return None
        return await service.get_config(
            ConfigParam(data_id=self.nacos_data_id, group=self.nacos_group)
        )

    async def _ensure_nacos_service(self) -> Any | None:
        if self._nacos_service is not None:
            return self._nacos_service

        try:
            from v2.nacos import ClientConfigBuilder, GRPCConfig, NacosConfigService
        except ImportError:
            logger.warning("nacos-sdk-python v2 is not installed; skip Nacos client init")
            return None

        try:
            client_config = (
                ClientConfigBuilder()
                .server_address(self.nacos_server_addr)
                .log_level("INFO")
                .grpc_config(GRPCConfig(grpc_timeout=5000))
                .build()
            )
            self._nacos_service = await NacosConfigService.create_config_service(client_config)
            return self._nacos_service
        except Exception as exc:
            logger.warning("Failed to initialize Nacos config service: %s", exc)
            return None


def create_config_manager_from_env() -> ConfigManager:
    default_config_path = Path(__file__).resolve().parent / "sample_config.yaml"
    return ConfigManager(
        config_path=os.getenv("AUTO_AUGMENT_CONFIG", str(default_config_path)),
        use_nacos=_as_bool(os.getenv("AUTO_AUGMENT_USE_NACOS"), default=False),
        nacos_server_addr=os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848"),
        nacos_data_id=os.getenv("NACOS_DATA_ID", "AUTO_AUGMENT_PIPELINE"),
        nacos_group=os.getenv("NACOS_GROUP", "DEFAULT_GROUP"),
        watch_nacos=_as_bool(os.getenv("AUTO_AUGMENT_WATCH_NACOS"), default=True),
    )
