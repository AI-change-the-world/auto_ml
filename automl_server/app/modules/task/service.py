"""任务服务 - 与 model_trainer 通信"""
import json
from typing import List, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import NotFoundException, BadRequestException
from app.utils.http_client import HttpClient
from app.config.settings import get_settings
from . import crud
from .schemas import TaskCreate, TaskResponse, TaskLogResponse, BaseModelResponse


class TaskService:
    def __init__(self):
        settings = get_settings()
        # model_trainer 服务地址
        self.trainer_url = "http://model-trainer:45680"  # 可从配置获取
        self.http_client = HttpClient(base_url=self.trainer_url, timeout=30)
    
    async def create_task(self, db: AsyncSession, data: TaskCreate) -> TaskResponse:
        """创建训练任务并通知 model_trainer"""
        # 保存任务到数据库
        task = await crud.create_task(
            db,
            task_type=data.task_type,
            dataset_id=data.dataset_id,
            annotation_id=data.annotation_id,
            config=data.config,
            status=0,  # PENDING
        )
        
        # 调用 model_trainer 启动训练
        try:
            config = json.loads(data.config) if data.config else {}
            train_request = {
                "task_id": task.id,
                "task_type": "detection" if data.task_type == 0 else "classification",
                "dataset_id": data.dataset_id,
                "annotation_id": data.annotation_id,
                **config,
            }
            
            response = await self.http_client.post("/train/start", json=train_request)
            if response.status_code != 200:
                logger.warning(f"Failed to start training: {response.text}")
            else:
                logger.info(f"Training task {task.id} started")
                
        except Exception as e:
            logger.error(f"Failed to communicate with model_trainer: {e}")
            # 任务已创建，trainer 会通过 MQ 更新状态
        
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


_service: Optional[TaskService] = None

def get_task_service() -> TaskService:
    global _service
    if _service is None:
        _service = TaskService()
    return _service
