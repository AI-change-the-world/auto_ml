"""
Model Trainer Service
轻量级模型训练服务，使用 RabbitMQ 接收任务和发送状态
"""
import json
import os
import threading
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.trainer import train_classification, train_detection
from utils.logger import logger
from utils.mq import get_mq_client, get_mq_config

SERVICE_NAME = "model-trainer"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Model Trainer Service starting...")

    # 初始化 MQ 连接
    try:
        mq_client = get_mq_client()
        logger.info("RabbitMQ connection established")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")

    # 启动 MQ 消费者（如果配置为消费者模式）
    if os.getenv("MQ_CONSUMER", "false").lower() == "true":
        consumer_thread = threading.Thread(
            target=start_mq_consumer, daemon=True)
        consumer_thread.start()
        logger.info("MQ consumer started")

    logger.info("Model Trainer Service started")
    yield

    # 关闭 MQ 连接
    try:
        get_mq_client().close()
    except Exception:
        pass

    logger.info("Model Trainer Service stopped")


app = FastAPI(
    title="Model Trainer Service",
    description="轻量级 YOLO 模型训练服务（基于 RabbitMQ）",
    version="2.0.0",
    lifespan=lifespan,
)


# ============ 请求/响应模型 ============

class TrainRequest(BaseModel):
    task_id: int
    dataset_path: str
    annotation_path: str
    classes: Optional[List[str]] = None
    task_config: Dict[str, Any]


class TrainResponse(BaseModel):
    task_id: int
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    mq_connected: bool


# ============ API 端点 ============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    mq_connected = False
    try:
        client = get_mq_client()
        mq_connected = client.connection is not None and not client.connection.is_closed
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        mq_connected=mq_connected
    )


@app.post("/train/detection", response_model=TrainResponse)
async def start_detection_training(request: TrainRequest):
    """
    启动目标检测模型训练

    训练状态和日志通过 RabbitMQ 发送，主服务负责写入数据库
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
            message="Detection training started, status will be sent via MQ",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start detection training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/train/classification", response_model=TrainResponse)
async def start_classification_training(request: TrainRequest):
    """
    启动分类模型训练

    训练状态和日志通过 RabbitMQ 发送，主服务负责写入数据库
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
            message="Classification training started, status will be sent via MQ",
        )
    except Exception as e:
        logger.error(f"Failed to start classification training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ MQ 消费者 ============

def start_mq_consumer():
    """
    启动 MQ 消费者，从队列接收训练任务

    消息格式:
    {
        "task_type": "detection" | "classification",
        "task_id": 1,
        "dataset_path": "...",
        "annotation_path": "...",
        "classes": [...],  // detection only
        "task_config": {...}
    }
    """
    import pika

    config = get_mq_config()

    try:
        credentials = pika.PlainCredentials(config.username, config.password)
        parameters = pika.ConnectionParameters(
            host=config.host,
            port=config.port,
            virtual_host=config.virtual_host,
            credentials=credentials,
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # 声明队列
        queue_name = "trainer.task.queue"
        channel.queue_declare(queue=queue_name, durable=True)

        # 绑定到交换机
        channel.queue_bind(
            queue=queue_name,
            exchange=config.exchange_name,
            routing_key="trainer.task.#",
        )

        logger.info(f"MQ consumer listening on queue: {queue_name}")

        def callback(ch, method, properties, body):
            try:
                data = json.loads(body)
                task_type = data.get("task_type", "detection")
                task_id = data["task_id"]

                logger.info(
                    f"Received task from MQ: task_id={task_id}, type={task_type}")

                if task_type == "detection":
                    train_detection(
                        task_id=task_id,
                        dataset_path=data["dataset_path"],
                        annotation_path=data["annotation_path"],
                        classes=data["classes"],
                        task_config=data["task_config"],
                    )
                elif task_type == "classification":
                    train_classification(
                        task_id=task_id,
                        dataset_path=data["dataset_path"],
                        annotation_path=data["annotation_path"],
                        task_config=data["task_config"],
                    )

                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                logger.error(f"Failed to process MQ message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        channel.start_consuming()

    except Exception as e:
        logger.error(f"MQ consumer error: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080)),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
