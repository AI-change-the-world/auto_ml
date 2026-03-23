"""
Model Trainer Service
轻量级模型训练服务，支持串行训练 YOLO 模型
"""
import json
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.trainer import get_training_status, train_classification, train_detection
from db.base import init_db
from utils.config import get_trainer_config
from utils.logger import logger


# 全局配置
trainer_config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    global trainer_config
    trainer_config = get_trainer_config()

    # 初始化数据库
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        init_db(db_url)
        logger.info("Database initialized")
    else:
        logger.warning("DATABASE_URL not set, database not initialized")

    logger.info("Model Trainer Service started")
    yield
    # 关闭时清理
    logger.info("Model Trainer Service stopped")


app = FastAPI(
    title="Model Trainer Service",
    description="轻量级 YOLO 模型训练服务",
    version="1.0.0",
    lifespan=lifespan,
)


# ============ 请求/响应模型 ============

class TrainRequest(BaseModel):
    task_id: int
    dataset_path: str
    annotation_path: str
    classes: Optional[List[str]] = None  # 检测任务需要
    task_config: Dict[str, Any]


class TrainResponse(BaseModel):
    task_id: int
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: int
    status: int
    task_type: Optional[str]
    logs: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    version: str


# ============ API 端点 ============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/train/detection", response_model=TrainResponse)
async def start_detection_training(request: TrainRequest):
    """
    启动目标检测模型训练

    task_config 示例:
    {
        "name": "yolo11n.pt",
        "epoch": 10,
        "size": 640,
        "batch": 8,
        "device": "cpu",
        "dataset_id": 1,
        "annotation_id": 1
    }
    """
    try:
        if not request.classes:
            raise HTTPException(
                status_code=400, detail="classes is required for detection task")

        logger.info(f"Starting detection training for task {request.task_id}")

        train_detection(
            task_id=request.task_id,
            dataset_path=request.dataset_path,
            annotation_path=request.annotation_path,
            classes=request.classes,
            task_config=request.task_config,
        )

        return TrainResponse(
            task_id=request.task_id,
            status="started",
            message="Detection training started successfully",
        )
    except Exception as e:
        logger.error(f"Failed to start detection training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/train/classification", response_model=TrainResponse)
async def start_classification_training(request: TrainRequest):
    """
    启动分类模型训练

    task_config 示例:
    {
        "name": "yolo11n-cls.pt",
        "epoch": 10,
        "size": 640,
        "batch": 8,
        "device": "cpu",
        "dataset_id": 1,
        "annotation_id": 1
    }
    """
    try:
        logger.info(
            f"Starting classification training for task {request.task_id}")

        train_classification(
            task_id=request.task_id,
            dataset_path=request.dataset_path,
            annotation_path=request.annotation_path,
            task_config=request.task_config,
        )

        return TrainResponse(
            task_id=request.task_id,
            status="started",
            message="Classification training started successfully",
        )
    except Exception as e:
        logger.error(f"Failed to start classification training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/train/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: int):
    """获取训练任务状态"""
    try:
        status = get_training_status(task_id)
        if status["status"] == "not_found":
            raise HTTPException(
                status_code=404, detail=f"Task {task_id} not found")

        return TaskStatusResponse(
            task_id=status["task_id"],
            status=status["status"],
            task_type=status.get("task_type"),
            logs=status["logs"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 消息队列消费者（可选） ============

def start_mq_consumer():
    """启动消息队列消费者"""
    mq_type = os.getenv("MQ_TYPE", "redis")

    if mq_type == "redis":
        try:
            import redis
            r = redis.from_url(os.getenv("MQ_URL", "redis://localhost:6379/0"))

            logger.info("Starting Redis MQ consumer...")

            while True:
                # 阻塞式获取消息
                result = r.blpop("model_trainer_queue", timeout=5)
                if result:
                    _, message = result
                    try:
                        data = json.loads(message)
                        task_type = data.get("task_type", "detection")

                        if task_type == "detection":
                            train_detection(
                                task_id=data["task_id"],
                                dataset_path=data["dataset_path"],
                                annotation_path=data["annotation_path"],
                                classes=data["classes"],
                                task_config=data["task_config"],
                            )
                        elif task_type == "classification":
                            train_classification(
                                task_id=data["task_id"],
                                dataset_path=data["dataset_path"],
                                annotation_path=data["annotation_path"],
                                task_config=data["task_config"],
                            )

                        logger.info(
                            f"Processed task {data['task_id']} from queue")
                    except Exception as e:
                        logger.error(f"Failed to process message: {e}")
        except ImportError:
            logger.warning("Redis not installed, MQ consumer not started")
        except Exception as e:
            logger.error(f"MQ consumer error: {e}")


if __name__ == "__main__":
    import uvicorn

    # 检查是否以 MQ 消费者模式启动
    if os.getenv("MQ_CONSUMER", "false").lower() == "true":
        start_mq_consumer()
    else:
        uvicorn.run(
            "server:app",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", 8080)),
            reload=os.getenv("RELOAD", "false").lower() == "true",
        )
