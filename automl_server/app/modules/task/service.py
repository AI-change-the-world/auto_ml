"""任务服务 - 与 model_trainer 通信"""
import asyncio
import json
from typing import List, Optional
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import NotFoundException, BadRequestException
from app.common.constants import TaskStatus, TaskType
from app.config.settings import get_settings
from app.db.models import Dataset, Annotation
from app.mq.publisher import get_publisher
from app.utils.http_client import HttpClient
from . import crud
from .schemas import TaskCreate, TaskResponse, TaskLogResponse, BaseModelResponse, TrainerStatusResponse


class TaskService:
    def __init__(self):
        settings = get_settings()
        self.publisher = get_publisher()
        self.trainer_client = HttpClient(
            base_url=settings.model_trainer.base_url,
            timeout=settings.model_trainer.timeout,
        )

    async def create_task(self, db: AsyncSession, data: TaskCreate) -> TaskResponse:
        """创建训练任务并通过 RabbitMQ 通知 model_trainer"""
        if data.annotation_id is None:
            raise BadRequestException("annotation_id is required for training")

        dataset = await db.scalar(
            select(Dataset).where(
                Dataset.id == data.dataset_id,
                Dataset.is_deleted == False,
            )
        )
        if not dataset:
            raise NotFoundException(f"Dataset {data.dataset_id} not found")

        annotation = await db.scalar(
            select(Annotation).where(
                Annotation.id == data.annotation_id,
                Annotation.is_deleted == False,
            )
        )
        if not annotation:
            raise NotFoundException(f"Annotation {data.annotation_id} not found")

        if not dataset.save_path:
            raise BadRequestException("dataset save_path is empty")
        if not annotation.save_path:
            raise BadRequestException("annotation save_path is empty")

        # 保存任务到数据库
        task = await crud.create_task(
            db,
            task_type=data.task_type,
            dataset_id=data.dataset_id,
            annotation_id=data.annotation_id,
            config=data.config,
            status=TaskStatus.PENDING,
        )
        await db.commit()
        await db.refresh(task)

        config = json.loads(data.config) if data.config else {}
        classes = self._parse_classes(annotation.classes)
        train_request = {
            "task_id": task.id,
            "task_type": "detection" if data.task_type == TaskType.DETECTION else "classification",
            "dataset_path": dataset.save_path,
            "annotation_path": annotation.save_path,
            "classes": classes,
            "task_config": {
                **config,
                "dataset_id": data.dataset_id,
                "annotation_id": data.annotation_id,
            },
        }

        # 通过 MQ 下发训练任务
        try:
            await asyncio.to_thread(self.publisher.publish_training_task, train_request)
            logger.info(f"Training task {task.id} queued by MQ")
        except Exception as e:
            logger.error(f"Failed to publish trainer task: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.add(task)
            await db.commit()
            await db.refresh(task)

        return TaskResponse.model_validate(task)

    async def get_task(self, db: AsyncSession, task_id: int) -> TaskResponse:
        task = await crud.get_task_by_id(db, task_id)
        if not task:
            raise NotFoundException(f"Task {task_id} not found")
        return TaskResponse.model_validate(task)

    async def list_tasks(self, db: AsyncSession, page: int = 1, page_size: int = 10, status: int = None) -> tuple[List[TaskResponse], int]:
        offset = (page - 1) * page_size
        items, total = await crud.get_tasks(db, offset, page_size, status)
        return [TaskResponse.model_validate(item) for item in items], total

    async def get_task_logs(self, db: AsyncSession, task_id: int, page: int = 1, page_size: int = 100) -> tuple[List[TaskLogResponse], int]:
        task = await crud.get_task_by_id(db, task_id)
        if not task:
            raise NotFoundException(f"Task {task_id} not found")

        offset = (page - 1) * page_size
        logs, total = await crud.get_task_logs(db, task_id, offset, page_size)
        return [TaskLogResponse.model_validate(log) for log in logs], total

    async def get_base_models(self, db: AsyncSession) -> List[BaseModelResponse]:
        models = await crud.get_base_models(db)
        return [BaseModelResponse.model_validate(m) for m in models]

    async def get_trainer_status(self) -> TrainerStatusResponse:
        try:
            response = await self.trainer_client.get("/health")
            if response.status_code != 200:
                return TrainerStatusResponse(
                    reachable=False,
                    status="unreachable",
                    message=f"model_trainer returned {response.status_code}",
                )
            payload = response.json()
            return TrainerStatusResponse(
                reachable=True,
                status=payload.get("status", "unknown"),
                version=payload.get("version"),
                mq_connected=bool(payload.get("mq_connected", False)),
                max_concurrent=int(payload.get("max_concurrent", 0) or 0),
                active_tasks=int(payload.get("active_tasks", 0) or 0),
                queued_tasks=int(payload.get("queued_tasks", 0) or 0),
            )
        except Exception as e:
            logger.warning(f"Failed to fetch trainer status: {e}")
            return TrainerStatusResponse(
                reachable=False,
                status="unreachable",
                message=str(e),
            )

    def _parse_classes(self, raw_classes: Optional[str]) -> List[str]:
        if not raw_classes:
            return []
        try:
            parsed = json.loads(raw_classes)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
        return [item.strip() for item in raw_classes.split(",") if item.strip()]


def get_task_service() -> TaskService:
    return TaskService()
