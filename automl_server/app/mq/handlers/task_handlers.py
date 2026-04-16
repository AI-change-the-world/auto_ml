"""
任务相关消息处理器
"""
from datetime import datetime
import json

from loguru import logger
from sqlalchemy import update

from app.common.constants import TaskStatus
from app.config.database import AsyncSessionLocal
from app.db.models import Task, TaskLog
from app.mq.messages import TaskStatusMessage, TaskLogMessage
from app.modules.task.service import TaskService
from app.modules.task.stream import StreamEvent, get_task_stream_hub


async def handle_task_status_update(message: TaskStatusMessage):
    """
    处理任务状态更新消息
    更新 Task 表的状态
    """
    logger.info(
        f"Handling task status update: task_id={message.task_id}, status={message.status}")

    async with AsyncSessionLocal() as session:
        try:
            # 构建更新数据
            update_data = {"status": message.status, "updated_at": datetime.now()}

            if message.status == TaskStatus.FAILED.value and message.message:
                update_data["error_message"] = message.message
            elif message.status != TaskStatus.FAILED.value:
                update_data["error_message"] = None

            if message.extra_data:
                # 合并到 result 字段
                update_data["result"] = json.dumps(message.extra_data)

            # 执行更新
            stmt = (
                update(Task)
                .where(Task.id == message.task_id)
                .where(Task.is_deleted == False)
                .values(**update_data)
            )
            await session.execute(stmt)
            await session.commit()

            task = await session.get(Task, message.task_id)
            if task is not None:
                task_payload = TaskService()._serialize_task(task).model_dump(mode="json")
                await get_task_stream_hub().publish(
                    StreamEvent(
                        event="task_upsert",
                        task_id=message.task_id,
                        data={
                            "task": task_payload
                        },
                    )
                )

            logger.info(
                f"Task {message.task_id} status updated to {message.status}")

        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            await session.rollback()
            raise


async def handle_task_log(message: TaskLogMessage):
    """
    处理任务日志消息
    写入 TaskLog 表
    """
    logger.debug(f"Handling task log: task_id={message.task_id}")

    async with AsyncSessionLocal() as session:
        try:
            # 创建日志记录
            log_entry = TaskLog(
                task_id=message.task_id,
                content=message.log_content,
                log_level=message.log_level,
            )
            session.add(log_entry)
            await session.commit()
            await session.refresh(log_entry)

            await get_task_stream_hub().publish(
                StreamEvent(
                    event="task_log",
                    task_id=message.task_id,
                    data={
                        "log": {
                            "id": log_entry.id,
                            "task_id": log_entry.task_id,
                            "content": log_entry.content,
                            "log_level": log_entry.log_level,
                            "created_at": log_entry.created_at or datetime.utcnow(),
                        }
                    },
                )
            )

            logger.debug(f"Task log saved for task {message.task_id}")

        except Exception as e:
            logger.error(f"Failed to save task log: {e}")
            await session.rollback()
            raise
