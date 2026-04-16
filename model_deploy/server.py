"""
Model Deploy Service
轻量级模型部署服务，使用 RabbitMQ 发送状态
"""
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from core.deploy_service import deploy_service
from core.runtime_manager import runtime_manager
from utils.config import get_deploy_config
from utils.config_center import get_config_center
from utils.logger import logger
from utils.mq import get_mq_client

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

    # 清理所有运行时实例
    for model_id in list(runtime_manager.get_all_instances().keys()):
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
    version="2.0.0",
    lifespan=lifespan,
)


# ============ 请求/响应模型 ============

class DeployRequest(BaseModel):
    model_id: int
    model_path: str  # S3 路径
    device: str = "cpu"
    version: str = "v1"


class DeployResponse(BaseModel):
    success: bool
    deployment_id: Optional[int] = None
    port: Optional[int] = None
    error: Optional[str] = None


class UndeployResponse(BaseModel):
    success: bool
    message: str


class DeploymentInfo(BaseModel):
    deployment_id: int
    model_id: int
    model_path: Optional[str] = None
    version: str
    status: str
    port: Optional[int] = None
    device: str


class PredictResponse(BaseModel):
    success: bool
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    mq_connected: bool


class DeploymentHealthResponse(BaseModel):
    healthy: bool
    model_id: Optional[int] = None
    port: Optional[int] = None
    pid: Optional[int] = None
    status: Optional[str] = None
    error: Optional[str] = None


# ============ API 端点 ============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    mq_connected = False
    try:
        client = get_mq_client()
        mq_connected = client.is_ready()
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        mq_connected=mq_connected
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
        result = deploy_service.deploy(
            model_id=request.model_id,
            model_path=request.model_path,
            device=request.device,
            version=request.version
        )

        if result["success"]:
            return DeployResponse(
                success=True,
                deployment_id=result.get("deployment_id"),
                port=result.get("port")
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
        result = deploy_service.undeploy(model_id)

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
        deployments = deploy_service.get_deployments()
        return [DeploymentInfo(**dep) for dep in deployments]
    except Exception as e:
        logger.error(f"List deployments failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/{model_id}", response_model=PredictResponse)
async def predict(model_id: int, file: UploadFile = File(...)):
    """
    执行模型推理

    - **model_id**: 模型业务ID
    - **file**: 图像文件
    """
    try:
        image_data = await file.read()
        result = deploy_service.predict(model_id, image_data)

        if result.get("success"):
            return PredictResponse(
                success=True,
                results=result.get("results", [])
            )
        else:
            return PredictResponse(
                success=False,
                error=result.get("error")
            )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/{model_id}/base64")
async def predict_base64(model_id: int, data: dict):
    """
    使用 base64 编码的图像进行推理

    - **model_id**: 模型业务ID
    - **image**: base64 编码的图像字符串
    """
    try:
        image_base64 = data.get("image")
        if not image_base64:
            raise HTTPException(
                status_code=400, detail="image field is required")

        result = deploy_service.predict_base64(model_id, image_base64)

        if result.get("success"):
            return PredictResponse(
                success=True,
                results=result.get("results", [])
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
        result = deploy_service.health_check(model_id)
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
        success = runtime_manager.restart_instance(model_id)
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
