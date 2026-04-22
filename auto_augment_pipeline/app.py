from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from config import create_config_manager_from_env
from models import ExecuteCapabilityRequest, InlinePipelineRunRequest, NamedPipelineRunRequest, TaskPayload
from mq import RabbitMQRpcWorker, load_rabbitmq_config
from service import AutoAugmentService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    config_manager = create_config_manager_from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config = await config_manager.load()
        service = AutoAugmentService(config)
        mq_config = load_rabbitmq_config()
        rpc_worker = RabbitMQRpcWorker(
            mq_config,
            lambda payload: handle_rpc_request(service, payload),
        )
        app.state.config_manager = config_manager
        app.state.service = service
        app.state.rpc_worker = rpc_worker
        await config_manager.start_watch(service.reload)
        rpc_worker.start()
        logger.info("Auto augment pipeline service is ready")
        yield
        rpc_worker.stop()
        await config_manager.close()

    app = FastAPI(
        title="Auto Augment Pipeline",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "Auto Augment Pipeline is running"}

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
        pipeline_name = str(payload.get("pipeline_name") or "").strip()
        if not pipeline_name:
            raise ValueError("pipeline_name is required")
        request_payload = NamedPipelineRunRequest.model_validate(payload.get("request") or {})
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
