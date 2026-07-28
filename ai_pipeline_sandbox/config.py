"""Configuration for the batch script sandbox."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


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


def _nested_value(mapping: dict[str, Any], section: str, key: str, fallback: str) -> str:
    value = mapping.get(section, {})
    if isinstance(value, dict) and value.get(key):
        return str(value[key])
    return fallback


def _load_nacos_payload() -> dict[str, Any]:
    if os.getenv("USE_NACOS", "true").lower() != "true":
        return {}
    try:
        import nacos

        runtime_dir = Path(os.getenv("PIPELINE_SANDBOX_WORKSPACE", "/app/runtime-data"))
        log_dir = runtime_dir / "nacos"
        log_dir.mkdir(parents=True, exist_ok=True)
        client = nacos.NacosClient(
            os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848"),
            namespace=os.getenv("NACOS_NAMESPACE", "public"),
            logDir=str(log_dir),
        )
        content = client.get_config(
            os.getenv("NACOS_DATA_ID", "AUTO_ML_CONFIG"),
            os.getenv("NACOS_GROUP", "AUTO_ML"),
        ) or ""
        parsed = yaml.safe_load(content) or {}
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def load_settings() -> SandboxSettings:
    payload = _load_nacos_payload()
    mq = payload.get("rabbitmq", {}) if isinstance(payload.get("rabbitmq"), dict) else {}
    queues = mq.get("queues", {}) if isinstance(mq.get("queues"), dict) else {}
    routing_keys = mq.get("routing_keys", {}) if isinstance(mq.get("routing_keys"), dict) else {}
    storage = payload.get("local-s3-config", {}) if isinstance(payload.get("local-s3-config"), dict) else {}

    workspace_root = Path(os.getenv("PIPELINE_SANDBOX_WORKSPACE", "/app/runtime-data"))
    return SandboxSettings(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8011")),
        workspace_root=workspace_root,
        scripts_root=Path(os.getenv("PIPELINE_SANDBOX_SCRIPTS", "/app/scripts")),
        timeout_seconds=int(os.getenv("PIPELINE_SANDBOX_TIMEOUT_SECONDS", "300")),
        max_output_bytes=int(os.getenv("PIPELINE_SANDBOX_MAX_OUTPUT_BYTES", str(2 * 1024 * 1024))),
        memory_bytes=int(os.getenv("PIPELINE_SANDBOX_MEMORY_BYTES", str(1024 * 1024 * 1024))),
        cpu_seconds=int(os.getenv("PIPELINE_SANDBOX_CPU_SECONDS", "300")),
        max_processes=int(os.getenv("PIPELINE_SANDBOX_MAX_PROCESSES", "32")),
        rabbitmq=RabbitSettings(
            host=os.getenv("RABBITMQ_HOST", str(mq.get("host", "localhost"))),
            port=int(os.getenv("RABBITMQ_PORT", str(mq.get("port", 5672)))),
            username=os.getenv("RABBITMQ_USER", str(mq.get("username", "guest"))),
            password=os.getenv("RABBITMQ_PASSWORD", str(mq.get("password", "guest"))),
            virtual_host=os.getenv("RABBITMQ_VHOST", str(mq.get("virtual_host", "/"))),
            exchange_name=os.getenv("RABBITMQ_EXCHANGE", str(mq.get("exchange_name", "auto_ml_exchange"))),
            exchange_type=os.getenv("RABBITMQ_EXCHANGE_TYPE", str(mq.get("exchange_type", "topic"))),
            execute_queue=os.getenv("PIPELINE_BATCH_EXECUTE_QUEUE", str(queues.get("pipeline_batch_execute", "auto_ml.pipeline.batch.execute"))),
            execute_routing_key=os.getenv("PIPELINE_BATCH_EXECUTE_ROUTING_KEY", str(routing_keys.get("pipeline_batch_execute", "pipeline.batch.execute"))),
            progress_routing_key=os.getenv("PIPELINE_BATCH_PROGRESS_ROUTING_KEY", str(routing_keys.get("pipeline_batch_progress", "pipeline.batch.progress"))),
            result_routing_key=os.getenv("PIPELINE_BATCH_RESULT_ROUTING_KEY", str(routing_keys.get("pipeline_batch_result", "pipeline.batch.result"))),
        ),
        storage=StorageSettings(
            endpoint=os.getenv("S3_ENDPOINT", str(storage.get("endpoint", "http://minio:9000"))),
            access_key=os.getenv("S3_ACCESS_KEY", str(storage.get("access_key", ""))),
            secret_key=os.getenv("S3_SECRET_KEY", str(storage.get("secret_key", ""))),
            region=os.getenv("S3_REGION", str(storage.get("region", "us-east-1"))),
            default_bucket=os.getenv("S3_DEFAULT_BUCKET", str(storage.get("bucket_name", "auto-ml-datasets"))),
            datasets_bucket=os.getenv("S3_DATASETS_BUCKET", str(storage.get("datasets_bucket_name", "auto-ml-datasets"))),
        ),
    )
