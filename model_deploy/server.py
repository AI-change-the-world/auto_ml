"""
Model Deploy Service
轻量级模型部署服务，使用 RabbitMQ 发送状态
"""
import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from core.deploy_service import deploy_service
from core.runtime_manager import runtime_manager
from utils.config import get_deploy_config
from utils.config_center import get_config_center
from utils.logger import logger
from utils.mq import get_mq_client
from utils.runtime_env import ensure_runtime_dependencies, runtime_dependency_status

SERVICE_NAME = "model-deploy"


def wait_for_mq_ready():
    retries = max(1, int(os.getenv("MQ_STARTUP_RETRIES", "12")))
    interval = max(1, int(os.getenv("MQ_STARTUP_RETRY_INTERVAL", "5")))
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            mq_client = get_mq_client()
            if mq_client.is_ready():
                logger.info(f"RabbitMQ ready on attempt {attempt}/{retries}")
                return
        except Exception as e:
            last_error = e
            logger.warning(
                f"RabbitMQ startup attempt {attempt}/{retries} failed: {e}"
            )
        if attempt < retries:
            time.sleep(interval)

    raise RuntimeError(
        f"Failed to connect to RabbitMQ after {retries} attempts: {last_error}"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Model Deploy Service starting...")

    try:
        message = ensure_runtime_dependencies()
        logger.info(f"Runtime dependency preflight passed: {message}")
    except Exception as e:
        logger.error(f"Runtime dependency preflight failed: {e}")
        raise

    get_config_center().start()

    # 初始化 MQ 连接
    try:
        wait_for_mq_ready()
        logger.info("RabbitMQ connection established")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        get_config_center().stop()
        raise

    # 确保模型缓存目录存在
    config = get_deploy_config()
    os.makedirs(config.model_cache_dir, exist_ok=True)

    logger.info("Model Deploy Service started")
    yield

    # 清理所有运行时实例，并尽量同步主服务中的部署状态
    for model_id in list(runtime_manager.get_all_instances().keys()):
        try:
            deploy_service.undeploy(model_id)
        except Exception as e:
            logger.error(f"Failed to publish undeploy on shutdown: model_id={model_id}, error={e}")
            runtime_manager.undeploy_model(model_id)

    # 关闭 MQ 连接
    try:
        get_mq_client().close()
    except Exception:
        pass
    get_config_center().stop()

    logger.info("Model Deploy Service stopped")


app = FastAPI(
    title="Model Deploy Service",
    description="轻量级模型部署服务（基于 RabbitMQ）",
    lifespan=lifespan,
)


# ============ 请求/响应模型 ============

class DeployRequest(BaseModel):
    model_id: int
    model_path: str  # S3 路径
    model_format: str = "onnx"
    task_kind: str = "detection_bbox"
    backend: str = "onnxruntime"
    device: str = "cpu"
    version: str = "v1"


class DeployResponse(BaseModel):
    success: bool
    deployment_id: Optional[int] = None
    port: Optional[int] = None
    model_format: Optional[str] = None
    task_kind: Optional[str] = None
    backend: Optional[str] = None
    error: Optional[str] = None


class UndeployResponse(BaseModel):
    success: bool
    message: str


class DeploymentInfo(BaseModel):
    deployment_id: int
    model_id: int
    model_path: Optional[str] = None
    model_format: Optional[str] = None
    task_kind: Optional[str] = None
    backend: Optional[str] = None
    version: str
    status: str
    port: Optional[int] = None
    device: str


class PredictResponse(BaseModel):
    success: bool
    task_kind: Optional[str] = None
    backend: Optional[str] = None
    device: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class InferenceParams(BaseModel):
    input_type: Optional[str] = Field(default=None, description="输入类型: tile/mosaic/raw_aerial")
    inference_mode: Optional[str] = Field(default=None, description="推理模式: direct/tile/scene")
    tile_size: Optional[int] = Field(default=None, ge=64, description="切片尺寸")
    tile_overlap: Optional[float] = Field(default=None, ge=0, lt=1, description="切片重叠比例")
    merge_strategy: Optional[str] = Field(default=None, description="结果融合方式: nms/wbf")
    merge_iou: Optional[float] = Field(default=None, ge=0, le=1, description="融合 IoU 阈值")
    edge_filter: Optional[bool] = Field(default=None, description="是否过滤切片边缘结果")
    return_global_coords: Optional[bool] = Field(default=None, description="是否返回全局坐标")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="保留扩展参数")


class PredictBase64Request(BaseModel):
    image: str
    inference_params: Optional[InferenceParams] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    mq_connected: bool
    runtime_dependencies_ok: bool
    runtime_dependencies_error: Optional[str] = None


class DeploymentHealthResponse(BaseModel):
    healthy: bool
    model_id: Optional[int] = None
    port: Optional[int] = None
    pid: Optional[int] = None
    status: Optional[str] = None
    task_kind: Optional[str] = None
    backend: Optional[str] = None
    device: Optional[str] = None
    error: Optional[str] = None


# ============ API 端点 ============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    mq_connected = False
    deps_ok = False
    deps_message = None
    try:
        client = get_mq_client()
        mq_connected = client.is_ready()
    except Exception:
        pass

    deps_ok, deps_message = runtime_dependency_status()

    return HealthResponse(
        status="healthy" if deps_ok else "unhealthy",
        version="2.0.0",
        mq_connected=mq_connected,
        runtime_dependencies_ok=deps_ok,
        runtime_dependencies_error=None if deps_ok else deps_message,
    )


@app.post("/deploy", response_model=DeployResponse)
async def deploy_model(request: DeployRequest):
    """
    部署模型

    - **model_id**: 模型业务ID
    - **model_path**: S3 上的模型路径
    - **device**: 运行设备 (cpu/cuda)
    - **version**: 版本号

    部署状态通过 RabbitMQ 发送，主服务负责写入数据库
    """
    try:
        logger.info(
            f"Deploying model {request.model_id} from {request.model_path}")
        result = await asyncio.to_thread(
            deploy_service.deploy,
            model_id=request.model_id,
            model_path=request.model_path,
            model_format=request.model_format,
            task_kind=request.task_kind,
            backend=request.backend,
            device=request.device,
            version=request.version,
        )

        if result["success"]:
            return DeployResponse(
                success=True,
                deployment_id=result.get("deployment_id"),
                port=result.get("port"),
                model_format=result.get("model_format"),
                task_kind=result.get("task_kind"),
                backend=result.get("backend"),
            )
        else:
            return DeployResponse(
                success=False,
                error=result.get("error")
            )
    except Exception as e:
        logger.error(f"Deploy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/undeploy/{model_id}", response_model=UndeployResponse)
async def undeploy_model(model_id: int):
    """
    卸载模型

    - **model_id**: 模型业务ID
    """
    try:
        logger.info(f"Undeploying model {model_id}")
        result = await asyncio.to_thread(deploy_service.undeploy, model_id)

        return UndeployResponse(
            success=result["success"],
            message=result.get("message", "")
        )
    except Exception as e:
        logger.error(f"Undeploy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/deployments", response_model=List[DeploymentInfo])
async def list_deployments():
    """获取所有部署列表（本地维护的状态）"""
    try:
        deployments = await asyncio.to_thread(deploy_service.get_deployments)
        return [DeploymentInfo(**dep) for dep in deployments]
    except Exception as e:
        logger.error(f"List deployments failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/{model_id}", response_model=PredictResponse)
async def predict(
    model_id: int,
    file: UploadFile = File(...),
    inference_params: str | None = Form(default=None),
):
    """
    执行模型推理

    - **model_id**: 模型业务ID
    - **file**: 图像文件
    """
    try:
        image_data = await file.read()
        parsed_params = None
        if inference_params:
            try:
                parsed_params = InferenceParams.model_validate(json.loads(inference_params))
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"invalid inference_params: {exc}") from exc

        result = await asyncio.to_thread(
            deploy_service.predict,
            model_id,
            image_data,
            parsed_params.model_dump(exclude_none=True) if parsed_params else None,
        )

        if result.get("success"):
            return PredictResponse(
                success=True,
                task_kind=result.get("task_kind"),
                backend=result.get("backend"),
                device=result.get("device"),
                image_width=result.get("image_width"),
                image_height=result.get("image_height"),
                results=result.get("results", []),
            )
        else:
            return PredictResponse(
                success=False,
                error=result.get("error")
            )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/{model_id}/base64", response_model=PredictResponse)
async def predict_base64(model_id: int, data: PredictBase64Request):
    """
    使用 base64 编码的图像进行推理

    - **model_id**: 模型业务ID
    - **image**: base64 编码的图像字符串
    """
    try:
        image_base64 = data.image
        if not image_base64:
            raise HTTPException(
                status_code=400, detail="image field is required")

        result = await asyncio.to_thread(
            deploy_service.predict_base64,
            model_id,
            image_base64,
            data.inference_params.model_dump(exclude_none=True) if data.inference_params else None,
        )

        if result.get("success"):
            return PredictResponse(
                success=True,
                task_kind=result.get("task_kind"),
                backend=result.get("backend"),
                device=result.get("device"),
                image_width=result.get("image_width"),
                image_height=result.get("image_height"),
                results=result.get("results", []),
            )
        else:
            return PredictResponse(
                success=False,
                error=result.get("error")
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/deploy/{model_id}/health", response_model=DeploymentHealthResponse)
async def deployment_health(model_id: int):
    """
    检查部署健康状态

    - **model_id**: 模型业务ID
    """
    try:
        result = await asyncio.to_thread(deploy_service.health_check, model_id)
        return DeploymentHealthResponse(**result)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/runtime/{model_id}/restart")
async def restart_runtime(model_id: int):
    """
    重启运行时实例

    - **model_id**: 模型业务ID
    """
    try:
        success = await asyncio.to_thread(runtime_manager.restart_instance, model_id)
        return {"success": success, "message": "Runtime restarted" if success else "Failed to restart runtime"}
    except Exception as e:
        logger.error(f"Restart failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8082)),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
