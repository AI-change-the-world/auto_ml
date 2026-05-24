from __future__ import annotations

import os
from contextlib import asynccontextmanager
from threading import RLock

from fastapi import FastAPI, HTTPException, Request
from loguru import logger

from config import get_runtime_config
from models import (
    ExecuteCapabilityRequest,
    InlinePipelineRunRequest,
    NamedPipelineRunRequest,
    PipelineDefinition,
    TaskPayload,
)
from logging_config import configure_logging
from mq import RabbitMQRpcWorker, load_rabbitmq_config
from service import AutoAugmentService

configure_logging("ai_pipeline_runtime")


def create_app() -> FastAPI:
    service_holder: dict[str, AutoAugmentService | None] = {"service": None}
    service_lock = RLock()

    def get_service() -> AutoAugmentService:
        with service_lock:
            service = service_holder["service"]
            if service is None:
                raise RuntimeError(
                    "AI pipeline runtime service is not initialized")
            return service

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config = get_runtime_config()
        service = AutoAugmentService(config)
        mq_config = load_rabbitmq_config()
        rpc_worker = RabbitMQRpcWorker(
            mq_config,
            lambda payload: handle_rpc_request(get_service(), payload),
        )
        with service_lock:
            service_holder["service"] = service
        app.state.service = service
        app.state.rpc_worker = rpc_worker
        rpc_worker.start()
        logger.info("AI pipeline runtime service is ready")
        yield
        rpc_worker.stop()
        with service_lock:
            service_holder["service"] = None

    app = FastAPI(
        title="AI Pipeline Runtime",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "AI Pipeline Runtime is running"}

    @app.get("/v1/capabilities")
    async def list_capabilities():
        return app.state.service.list_capabilities()

    @app.get("/v1/pipelines")
    async def list_pipelines():
        return app.state.service.list_pipelines()

    @app.post("/v1/capabilities/{capability_name}/run")
    async def run_capability(capability_name: str, request: ExecuteCapabilityRequest):
        try:
            return app.state.service.execute_capability(capability_name, request)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/pipelines/{pipeline_name}/run")
    async def run_named_pipeline(pipeline_name: str, request: Request):
        try:
            body = await request.json()
            if isinstance(body, dict) and "input" in body:
                payload = NamedPipelineRunRequest.model_validate(body)
                return app.state.service.run_pipeline(
                    name=pipeline_name,
                    payload=payload.input,
                    params=payload.params,
                )
            return app.state.service.run_pipeline(
                name=pipeline_name,
                payload=TaskPayload.model_validate(body),
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/pipelines/run")
    async def run_inline_pipeline(request: InlinePipelineRunRequest):
        try:
            return app.state.service.run_pipeline(
                definition=request.definition,
                payload=request.input,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


def handle_rpc_request(service: AutoAugmentService, payload: dict):
    action = str(payload.get("action") or "").strip()
    if action == "list_pipelines":
        return [item.model_dump(mode="json") for item in service.list_pipelines()]
    if action == "run_pipeline":
        request_payload = NamedPipelineRunRequest.model_validate(
            payload.get("request") or {})
        definition_payload = payload.get("definition")
        if definition_payload is not None:
            definition = PipelineDefinition.model_validate(definition_payload)
            result = service.run_pipeline(
                definition=definition,
                payload=request_payload.input,
                params=request_payload.params,
            )
        else:
            pipeline_name = str(payload.get("pipeline_name") or "").strip()
            if not pipeline_name:
                raise ValueError("pipeline_name is required")
            result = service.run_pipeline(
                name=pipeline_name,
                payload=request_payload.input,
                params=request_payload.params,
            )
        if hasattr(result, "model_dump"):
            return result.model_dump(mode="json")
        return result
    raise ValueError(f"unsupported rpc action `{action}`")


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8010)),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
