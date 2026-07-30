from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from batch_worker import BatchSandboxWorker
from config import load_settings
from logging_config import configure_logging
from nacos_config_center import get_config_center
from loguru import logger


configure_logging()
settings = load_settings()
worker = BatchSandboxWorker(settings)


def update_execution_limits(_old_config: dict, new_config: dict) -> None:
    next_settings = load_settings(new_config)
    worker.update_execution_limits(next_settings)
    logger.info(
        "Applied sandbox execution configuration: timeout_seconds={}, memory_bytes={}, cpu_seconds={}, max_processes={}",
        next_settings.timeout_seconds,
        next_settings.memory_bytes,
        next_settings.cpu_seconds,
        next_settings.max_processes,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting AI Pipeline Sandbox")
    config_center = get_config_center()
    config_center.register_callback("ai_pipeline_sandbox_limits", update_execution_limits)
    config_center.start()
    worker.update_execution_limits(load_settings(config_center.get_config_data()))
    worker.start()
    yield
    logger.info("Stopping AI Pipeline Sandbox")
    worker.stop()
    config_center.unregister_callback("ai_pipeline_sandbox_limits")
    config_center.stop()


app = FastAPI(title="AI Pipeline Batch Sandbox", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    if not worker.is_connected:
        raise HTTPException(status_code=503, detail="RabbitMQ worker is not connected")
    return {
        "status": "ok",
        "service": "ai_pipeline_sandbox",
        "active_chunks": worker.active_chunks,
        "execute_queue": worker.settings.rabbitmq.execute_queue,
    }
