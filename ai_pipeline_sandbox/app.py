from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from batch_worker import BatchSandboxWorker
from config import load_settings


settings = load_settings()
worker = BatchSandboxWorker(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    worker.start()
    yield
    worker.stop()


app = FastAPI(title="AI Pipeline Batch Sandbox", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ai_pipeline_sandbox",
        "active_chunks": worker.active_chunks,
        "execute_queue": settings.rabbitmq.execute_queue,
    }
