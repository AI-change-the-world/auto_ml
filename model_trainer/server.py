"""
Model Trainer Service
轻量级模型训练服务，使用 RabbitMQ 接收任务和发送状态
"""
import json
import os
import queue
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pika
from fastapi import FastAPI
from pydantic import BaseModel, Field

from core.trainer import run_classification_task, run_detection_task
from utils.config_center import get_config_center
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
consumer_stop_event = threading.Event()
consumer_connection_lock = threading.RLock()
consumer_connection: Optional[pika.BlockingConnection] = None
consumer_channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
consumer_ready_event = threading.Event()
consumer_last_error: Optional[Exception] = None


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

    def submit(self, payload: Dict[str, Any]) -> TrainingTask:
        task = TrainingTask(**payload)
        self._queue.put(TrainingEnvelope(task=task))
        try:
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
        except Exception as e:
            logger.warning(
                f"Training task {task.task_id} queued but failed to publish queue log: {e}"
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

            try:
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
            except Exception as e:
                logger.warning(
                    f"Task {task.task_id} dequeued but failed to publish queue log: {e}"
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
    get_config_center().register_callback(
        "model_trainer_mq_consumer",
        _on_config_update,
    )
    get_config_center().start()
    consumer_stop_event.clear()
    consumer_ready_event.clear()

    # 初始化 MQ 连接
    try:
        wait_for_mq_ready()
        logger.info("RabbitMQ connection established")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        get_config_center().stop()
        raise

    max_concurrent = int(os.getenv("TRAINER_MAX_CONCURRENT", "1"))
    task_dispatcher = TrainingDispatcher(max_concurrent=max_concurrent)
    task_dispatcher.start()

    # 启动 MQ 消费者
    consumer_thread = threading.Thread(
        target=start_mq_consumer,
        daemon=True,
    )
    consumer_thread.start()
    wait_for_consumer_ready()
    logger.info("MQ consumer started")

    logger.info("Model Trainer Service started")
    yield

    # 关闭 MQ 连接
    try:
        if task_dispatcher is not None:
            task_dispatcher.stop()
    except Exception:
        pass
    consumer_stop_event.set()
    close_consumer_connection()
    get_config_center().unregister_callback("model_trainer_mq_consumer")
    try:
        get_mq_client().close()
    except Exception:
        pass
    get_config_center().stop()

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
    mq_publish_connected: bool = False
    mq_consumer_connected: bool = False
    max_concurrent: int
    active_tasks: int
    queued_tasks: int


# ============ API 端点 ============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    mq_publish_connected = False
    try:
        client = get_mq_client()
        mq_publish_connected = client.is_ready()
    except Exception:
        pass

    with consumer_connection_lock:
        mq_consumer_connected = (
            consumer_ready_event.is_set()
            and consumer_connection is not None
            and not consumer_connection.is_closed
            and consumer_channel is not None
            and not consumer_channel.is_closed
        )

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        mq_connected=mq_consumer_connected,
        mq_publish_connected=mq_publish_connected,
        mq_consumer_connected=mq_consumer_connected,
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
    global consumer_connection, consumer_channel, consumer_last_error

    if task_dispatcher is None:
        raise RuntimeError("Training dispatcher is not initialized")
    retries = max(1, int(os.getenv("MQ_STARTUP_RETRIES", "12")))
    interval = max(1, int(os.getenv("MQ_STARTUP_RETRY_INTERVAL", "5")))
    attempts = 0

    while not consumer_stop_event.is_set():
        config = get_mq_config()
        try:
            credentials = pika.PlainCredentials(config.username, config.password)
            parameters = pika.ConnectionParameters(
                host=config.host,
                port=config.port,
                virtual_host=config.virtual_host,
                credentials=credentials,
                heartbeat=60,
                blocked_connection_timeout=300,
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            with consumer_connection_lock:
                consumer_connection = connection
                consumer_channel = channel
                consumer_last_error = None

            queue_name = config.trainer_task_queue
            channel.queue_declare(queue=queue_name, durable=True)
            channel.queue_bind(
                queue=queue_name,
                exchange=config.exchange_name,
                routing_key=config.trainer_task_routing_key,
            )

            logger.info(f"MQ consumer listening on queue: {queue_name}")
            consumer_ready_event.set()

            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body)
                    task_type = data.get("task_type", "detection")
                    task_id = data["task_id"]

                    logger.info(
                        f"Received task from MQ: task_id={task_id}, type={task_type}"
                    )
                    task_dispatcher.submit(data)
                    ch.basic_ack(delivery_tag=method.delivery_tag)

                except Exception as e:
                    logger.error(f"Failed to process MQ message: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_qos(prefetch_count=max(1, task_dispatcher.max_concurrent))
            channel.basic_consume(queue=queue_name, on_message_callback=callback)

            attempts = 0
            while not consumer_stop_event.is_set():
                connection.process_data_events(time_limit=1)
        except Exception as e:
            attempts += 1
            logger.error(f"MQ consumer error: {e}")
            consumer_last_error = e
            consumer_ready_event.clear()
            close_consumer_connection()
            if attempts >= retries:
                logger.error(
                    f"MQ consumer exceeded retry limit: {attempts}/{retries}"
                )
                break
            if not consumer_stop_event.wait(interval):
                continue
        finally:
            close_consumer_connection()


def close_consumer_connection():
    global consumer_connection, consumer_channel
    with consumer_connection_lock:
        if consumer_channel and not consumer_channel.is_closed:
            try:
                consumer_channel.close()
            except Exception:
                pass
        if consumer_connection and not consumer_connection.is_closed:
            try:
                consumer_connection.close()
            except Exception:
                pass
        consumer_channel = None
        consumer_connection = None
        consumer_ready_event.clear()


def _on_config_update(old_config: dict, new_config: dict):
    old_mq = (old_config or {}).get("rabbitmq", {})
    new_mq = (new_config or {}).get("rabbitmq", {})
    if old_mq == new_mq:
        return

    logger.info("RabbitMQ config changed, trainer consumer will reconnect")
    close_consumer_connection()


def wait_for_mq_ready():
    retries = max(1, int(os.getenv("MQ_STARTUP_RETRIES", "12")))
    interval = max(1, int(os.getenv("MQ_STARTUP_RETRY_INTERVAL", "5")))
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            client = get_mq_client()
            if client.is_ready():
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


def wait_for_consumer_ready():
    retries = max(1, int(os.getenv("MQ_STARTUP_RETRIES", "12")))
    interval = max(1, int(os.getenv("MQ_STARTUP_RETRY_INTERVAL", "5")))
    timeout = retries * interval + 5
    if consumer_ready_event.wait(timeout=timeout):
        return
    raise RuntimeError(
        f"Failed to start MQ consumer within {timeout}s: {consumer_last_error}"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8081)),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
