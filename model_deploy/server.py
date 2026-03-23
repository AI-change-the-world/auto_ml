"""
Model Deploy Service
轻量级模型部署服务，管理模型运行时实例
"""
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from core.deploy_service import deploy_service
from core.runtime_manager import runtime_manager
from db.base import init_db
from utils.config import get_deploy_config
from utils.logger import logger


# 全局配置
deploy_config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global deploy_config
    deploy_config = get_deploy_config()

    # 初始化数据库
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        init_db(db_url)
        logger.info("Database initialized")
    else:
        logger.warning("DATABASE_URL not set, database not initialized")

    logger.info("Model Deploy Service started")
    yield

    # 清理所有运行时实例
    for model_id in list(runtime_manager.get_all_instances().keys()):
        runtime_manager.undeploy_model(model_id)

    logger.info("Model Deploy Service stopped")


app = FastAPI(
    title="Model Deploy Service",
    description="轻量级模型部署服务",
    version="1.0.0",
    lifespan=lifespan,
)


# ============ 请求/响应模型 ============

class DeployRequest(BaseModel):
    model_id: int
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
    model_name: Optional[str]
    version: str
    status: str
    port: Optional[int]
    device: str
    created_at: Optional[Any]


class PredictResponse(BaseModel):
    success: bool
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str


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
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/deploy", response_model=DeployResponse)
async def deploy_model(request: DeployRequest):
    """
    部署模型

    - **model_id**: 模型ID
    - **device**: 运行设备 (cpu/cuda)
    - **version**: 版本号
    """
    try:
        logger.info(f"Deploying model {request.model_id}")
        result = deploy_service.deploy(
            model_id=request.model_id,
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


@app.post("/undeploy/{deployment_id}", response_model=UndeployResponse)
async def undeploy_model(deployment_id: int):
    """
    卸载模型

    - **deployment_id**: 部署ID
    """
    try:
        logger.info(f"Undeploying deployment {deployment_id}")
        result = deploy_service.undeploy(deployment_id)

        return UndeployResponse(
            success=result["success"],
            message=result.get("message", "")
        )
    except Exception as e:
        logger.error(f"Undeploy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/deployments", response_model=List[DeploymentInfo])
async def list_deployments():
    """获取所有部署列表"""
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

    - **model_id**: 模型ID
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

    - **model_id**: 模型ID
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

    - **model_id**: 模型ID
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

    - **model_id**: 模型ID
    """
    try:
        success = runtime_manager.restart_instance(model_id)
        return {"success": success, "message": "Runtime restarted" if success else "Failed to restart runtime"}
    except Exception as e:
        logger.error(f"Restart failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 模型转换工具 ============

@app.post("/convert/yolo-to-onnx")
async def convert_yolo_to_onnx(data: dict):
    """
    将 YOLO .pt 模型转换为 ONNX 格式

    - **pt_path**: .pt 文件路径
    - **output_path**: 输出 ONNX 文件路径（可选）
    """
    try:
        pt_path = data.get("pt_path")
        if not pt_path or not os.path.exists(pt_path):
            raise HTTPException(status_code=400, detail="Invalid pt_path")

        output_path = data.get("output_path", pt_path.replace(".pt", ".onnx"))

        # 使用 ultralytics 导出 ONNX
        from ultralytics import YOLO

        model = YOLO(pt_path)
        model.export(format="onnx", imgsz=640)

        return {
            "success": True,
            "output_path": output_path,
            "message": f"Model converted successfully to {output_path}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080)),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
