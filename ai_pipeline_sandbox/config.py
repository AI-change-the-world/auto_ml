"""Configuration for the batch script sandbox."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nacos_config_center import get_config_center


@dataclass(frozen=True)
class RabbitSettings:
    host: str
    port: int
    username: str
    password: str
    virtual_host: str
    exchange_name: str
    exchange_type: str
    execute_queue: str
    execute_routing_key: str
    progress_routing_key: str
    result_routing_key: str


@dataclass(frozen=True)
class StorageSettings:
    endpoint: str
    access_key: str
    secret_key: str
    region: str
    default_bucket: str
    datasets_bucket: str


@dataclass(frozen=True)
class SandboxSettings:
    host: str
    port: int
    workspace_root: Path
    scripts_root: Path
    timeout_seconds: int
    max_output_bytes: int
    memory_bytes: int
    cpu_seconds: int
    max_processes: int
    rabbitmq: RabbitSettings
    storage: StorageSettings


def _section(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    value = mapping.get(key)
    return value if isinstance(value, dict) else {}


def _config_value(
    config: dict[str, Any],
    key: str,
    env_name: str,
    fallback: str,
) -> str:
    value = config.get(key)
    if value is not None and value != "":
        return str(value)
    return os.getenv(env_name, fallback)


def _config_value_from_sections(
    sections: tuple[dict[str, Any], ...],
    key: str,
    env_name: str,
    fallback: str,
) -> str:
    for section in sections:
        value = section.get(key)
        if value is not None and value != "":
            return str(value)
    return os.getenv(env_name, fallback)


def _build_settings(payload: dict[str, Any]) -> SandboxSettings:
    mq = _section(payload, "rabbitmq")
    queues = _section(mq, "queues")
    routing_keys = _section(mq, "routing_keys")
    storage = _section(payload, "local-s3-config")
    sandbox = _section(payload, "ai-pipeline-sandbox")
    sandbox_mq = _section(sandbox, "rabbitmq")
    sandbox_storage = _section(sandbox, "storage")

    workspace_root = Path(os.getenv("PIPELINE_SANDBOX_WORKSPACE", "/app/runtime-data"))
    return SandboxSettings(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8011")),
        workspace_root=workspace_root,
        scripts_root=Path(os.getenv("PIPELINE_SANDBOX_SCRIPTS", "/app/scripts")),
        timeout_seconds=int(_config_value(sandbox, "timeout_seconds", "PIPELINE_SANDBOX_TIMEOUT_SECONDS", "300")),
        max_output_bytes=int(_config_value(sandbox, "max_output_bytes", "PIPELINE_SANDBOX_MAX_OUTPUT_BYTES", str(2 * 1024 * 1024))),
        memory_bytes=int(_config_value(sandbox, "memory_bytes", "PIPELINE_SANDBOX_MEMORY_BYTES", str(1024 * 1024 * 1024))),
        cpu_seconds=int(_config_value(sandbox, "cpu_seconds", "PIPELINE_SANDBOX_CPU_SECONDS", "300")),
        max_processes=int(_config_value(sandbox, "max_processes", "PIPELINE_SANDBOX_MAX_PROCESSES", "32")),
        rabbitmq=RabbitSettings(
            host=_config_value_from_sections((sandbox_mq, mq), "host", "RABBITMQ_HOST", "localhost"),
            port=int(_config_value_from_sections((sandbox_mq, mq), "port", "RABBITMQ_PORT", "5672")),
            username=_config_value_from_sections((sandbox_mq, mq), "username", "RABBITMQ_USER", "guest"),
            password=_config_value_from_sections((sandbox_mq, mq), "password", "RABBITMQ_PASSWORD", "guest"),
            virtual_host=_config_value_from_sections((sandbox_mq, mq), "virtual_host", "RABBITMQ_VHOST", "/"),
            exchange_name=_config_value_from_sections((sandbox_mq, mq), "exchange_name", "RABBITMQ_EXCHANGE", "auto_ml_exchange"),
            exchange_type=_config_value_from_sections((sandbox_mq, mq), "exchange_type", "RABBITMQ_EXCHANGE_TYPE", "topic"),
            execute_queue=_config_value_from_sections((sandbox_mq, queues), "pipeline_batch_execute", "PIPELINE_BATCH_EXECUTE_QUEUE", "auto_ml.pipeline.batch.execute"),
            execute_routing_key=_config_value_from_sections((sandbox_mq, routing_keys), "pipeline_batch_execute", "PIPELINE_BATCH_EXECUTE_ROUTING_KEY", "pipeline.batch.execute"),
            progress_routing_key=_config_value_from_sections((sandbox_mq, routing_keys), "pipeline_batch_progress", "PIPELINE_BATCH_PROGRESS_ROUTING_KEY", "pipeline.batch.progress"),
            result_routing_key=_config_value_from_sections((sandbox_mq, routing_keys), "pipeline_batch_result", "PIPELINE_BATCH_RESULT_ROUTING_KEY", "pipeline.batch.result"),
        ),
        storage=StorageSettings(
            endpoint=_config_value_from_sections((sandbox_storage, storage), "endpoint", "S3_ENDPOINT", "http://minio:9000"),
            access_key=_config_value_from_sections((sandbox_storage, storage), "access_key", "S3_ACCESS_KEY", ""),
            secret_key=_config_value_from_sections((sandbox_storage, storage), "secret_key", "S3_SECRET_KEY", ""),
            region=_config_value_from_sections((sandbox_storage, storage), "region", "S3_REGION", "us-east-1"),
            default_bucket=_config_value_from_sections((sandbox_storage, storage), "bucket_name", "S3_DEFAULT_BUCKET", "auto-ml-datasets"),
            datasets_bucket=_config_value_from_sections((sandbox_storage, storage), "datasets_bucket_name", "S3_DATASETS_BUCKET", "auto-ml-datasets"),
        ),
    )


def load_settings(config_data: dict[str, Any] | None = None) -> SandboxSettings:
    return _build_settings(config_data if config_data is not None else get_config_center().get_config_data())
