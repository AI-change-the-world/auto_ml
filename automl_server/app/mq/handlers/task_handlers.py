"""
任务相关消息处理器
"""
from loguru import logger
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import AsyncSessionLocal
from app.db.models import Task, TaskLog
from app.mq.messages import TaskStatusMessage, TaskLogMessage


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
            update_data = {"status": message.status}

            if message.message:
                update_data["error_message"] = message.message

            if message.extra_data:
                import json
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

            logger.debug(f"Task log saved for task {message.task_id}")

        except Exception as e:
            logger.error(f"Failed to save task log: {e}")
            await session.rollback()
            raise
