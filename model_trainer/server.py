"""
Model Trainer Service
轻量级模型训练服务，使用 RabbitMQ 接收任务和发送状态
"""
import json
import os
import queue
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from core.trainer import run_classification_task, run_detection_task
from utils.logger import logger
from utils.mq import (
    TaskStatus,
    get_mq_client,
    get_mq_config,
    publish_task_log,
    publish_task_status,
)

SERVICE_NAME = "model-trainer"
task_dispatcher: Optional["TrainingDispatcher"] = None


class TrainingTask(BaseModel):
    task_id: int
    task_type: str
    dataset_path: str
    annotation_path: str
    classes: Optional[List[str]] = None
    task_config: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class TrainingEnvelope:
    task: TrainingTask
    ack: Callable[[], None]


class TrainingDispatcher:
    """本地训练任务调度器，负责并发控制"""

    def __init__(self, max_concurrent: int):
        self.max_concurrent = max(1, max_concurrent)
        self._queue: "queue.Queue[Optional[TrainingEnvelope]]" = queue.Queue()
        self._workers: List[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()
        self._active_tasks = 0

    @property
    def active_tasks(self) -> int:
        with self._lock:
            return self._active_tasks

    @property
    def queued_tasks(self) -> int:
        return self._queue.qsize()

    def start(self):
        if self._running:
            return
        self._running = True
        self._workers = []
        for idx in range(self.max_concurrent):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(idx + 1,),
                daemon=True,
            )
            worker.start()
            self._workers.append(worker)
        logger.info(
            f"Training dispatcher started with max_concurrent={self.max_concurrent}"
        )

    def stop(self):
        if not self._running:
            return
        self._running = False
        for _ in self._workers:
            self._queue.put(None)
        for worker in self._workers:
            worker.join(timeout=5)
        self._workers = []
        logger.info("Training dispatcher stopped")

    def submit(self, payload: Dict[str, Any], ack: Callable[[], None]) -> TrainingTask:
        task = TrainingTask(**payload)
        self._queue.put(TrainingEnvelope(task=task, ack=ack))
        publish_task_log(
            task.task_id,
            (
                "[queue] Training task queued: "
                f"type={task.task_type}, "
                f"active={self.active_tasks}, "
                f"queued={self.queued_tasks}, "
                f"max_concurrent={self.max_concurrent}"
            ),
            SERVICE_NAME,
        )
        return task

    def _worker_loop(self, worker_id: int):
        while True:
            envelope = self._queue.get()
            if envelope is None:
                self._queue.task_done()
                break
            task = envelope.task

            with self._lock:
                self._active_tasks += 1
                active = self._active_tasks
                queued = self._queue.qsize()

            publish_task_log(
                task.task_id,
                (
                    "[queue] Training task dequeued: "
                    f"worker={worker_id}, "
                    f"active={active}, "
                    f"queued={queued}"
                ),
                SERVICE_NAME,
            )

            try:
                self._run_task(task)
            except Exception as e:
                logger.error(f"Unhandled dispatcher error for task {task.task_id}: {e}")
                publish_task_status(task.task_id, TaskStatus.FAILED, SERVICE_NAME, str(e))
                publish_task_log(
                    task.task_id,
                    f"[error] Dispatcher failed before training start: {e}",
                    SERVICE_NAME,
                    "ERROR",
                )
            finally:
                with self._lock:
                    self._active_tasks -= 1
                try:
                    envelope.ack()
                except Exception as e:
                    logger.error(f"Failed to ack MQ message for task {task.task_id}: {e}")
                self._queue.task_done()

    def _run_task(self, task: TrainingTask):
        if task.task_type == "detection":
            if not task.classes:
                raise ValueError("classes is required for detection task")
            run_detection_task(
                task_id=task.task_id,
                dataset_path=task.dataset_path,
                annotation_path=task.annotation_path,
                classes=task.classes,
                task_config=task.task_config,
            )
            return

        if task.task_type == "classification":
            run_classification_task(
                task_id=task.task_id,
                dataset_path=task.dataset_path,
                annotation_path=task.annotation_path,
                task_config=task.task_config,
            )
            return

        raise ValueError(f"Unsupported task_type: {task.task_type}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Model Trainer Service starting...")
    global task_dispatcher

    # 初始化 MQ 连接
    try:
        get_mq_client()
        logger.info("RabbitMQ connection established")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")

    max_concurrent = int(os.getenv("TRAINER_MAX_CONCURRENT", "1"))
    task_dispatcher = TrainingDispatcher(max_concurrent=max_concurrent)
    task_dispatcher.start()

    # 启动 MQ 消费者
    consumer_thread = threading.Thread(
        target=start_mq_consumer,
        daemon=True,
    )
    consumer_thread.start()
    logger.info("MQ consumer started")

    logger.info("Model Trainer Service started")
    yield

    # 关闭 MQ 连接
    try:
        if task_dispatcher is not None:
            task_dispatcher.stop()
    except Exception:
        pass
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


class HealthResponse(BaseModel):
    status: str
    version: str
    mq_connected: bool
    max_concurrent: int
    active_tasks: int
    queued_tasks: int


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
        mq_connected=mq_connected,
        max_concurrent=task_dispatcher.max_concurrent if task_dispatcher else 0,
        active_tasks=task_dispatcher.active_tasks if task_dispatcher else 0,
        queued_tasks=task_dispatcher.queued_tasks if task_dispatcher else 0,
    )


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
    if task_dispatcher is None:
        raise RuntimeError("Training dispatcher is not initialized")

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
        queue_name = config.trainer_task_queue
        channel.queue_declare(queue=queue_name, durable=True)

        # 绑定到交换机
        channel.queue_bind(
            queue=queue_name,
            exchange=config.exchange_name,
            routing_key=config.trainer_task_routing_key,
        )

        logger.info(f"MQ consumer listening on queue: {queue_name}")

        def callback(ch, method, properties, body):
            try:
                data = json.loads(body)
                task_type = data.get("task_type", "detection")
                task_id = data["task_id"]

                logger.info(
                    f"Received task from MQ: task_id={task_id}, type={task_type}")
                ack = partial(
                    connection.add_callback_threadsafe,
                    partial(ch.basic_ack, delivery_tag=method.delivery_tag),
                )
                task_dispatcher.submit(data, ack=ack)

            except Exception as e:
                logger.error(f"Failed to process MQ message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_qos(prefetch_count=max(1, task_dispatcher.max_concurrent))
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
