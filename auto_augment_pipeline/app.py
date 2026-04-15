from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .config import create_config_manager_from_env
from .models import ExecuteCapabilityRequest, InlinePipelineRunRequest, TaskPayload
from .service import AutoAugmentService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    config_manager = create_config_manager_from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config = await config_manager.load()
        service = AutoAugmentService(config)
        app.state.config_manager = config_manager
        app.state.service = service
        await config_manager.start_watch(service.reload)
        logger.info("Auto augment pipeline service is ready")
        yield
        await config_manager.close()

    app = FastAPI(
        title="Auto Augment Pipeline",
        version="2.0.0-dev",
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
    async def run_named_pipeline(pipeline_name: str, payload: TaskPayload):
        try:
            return app.state.service.run_pipeline(name=pipeline_name, payload=payload)
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


app = create_app()
