"""
模型相关消息处理器
"""
from loguru import logger
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import AsyncSessionLocal
from app.db.models import AvailableModel
from app.mq.messages import ModelRegisteredMessage, ModelDeployedMessage, ModelUndeployedMessage


async def handle_model_registered(message: ModelRegisteredMessage):
    """
    处理模型注册消息
    创建 AvailableModel 记录
    """
    logger.info(f"Handling model registered: task_id={message.task_id}")
    
    model_info = message.model_info
    
    async with AsyncSessionLocal() as session:
        try:
            # 创建可用模型记录
            model = AvailableModel(
                name=model_info.get("base_model_name", ""),
                model_path=model_info.get("save_path", ""),
                model_type=model_info.get("model_type", ""),
                dataset_id=model_info.get("dataset_id"),
                task_id=message.task_id,
                loss=model_info.get("loss"),
            )
            session.add(model)
            await session.commit()
            
            logger.info(f"Model registered: {model.name}, path={model.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            await session.rollback()
            raise


async def handle_model_deployed(message: ModelDeployedMessage):
    """
    处理模型部署消息
    更新 AvailableModel 的部署状态
    """
    logger.info(f"Handling model deployed: model_id={message.model_id}")
    
    deployment_info = message.deployment_info
    
    async with AsyncSessionLocal() as session:
        try:
            # 更新部署状态
            stmt = (
                update(AvailableModel)
                .where(AvailableModel.id == message.model_id)
                .where(AvailableModel.is_deleted == False)
                .values(
                    is_deployed=True,
                    deployment_id=deployment_info.get("deployment_id"),
                    deployment_port=deployment_info.get("port"),
                    deployment_version=deployment_info.get("version"),
                    deployment_device=deployment_info.get("device"),
                )
            )
            await session.execute(stmt)
            await session.commit()
            
            logger.info(f"Model {message.model_id} deployed at port {deployment_info.get('port')}")
            
        except Exception as e:
            logger.error(f"Failed to update model deployment status: {e}")
            await session.rollback()
            raise


async def handle_model_undeployed(message: ModelUndeployedMessage):
    """
    处理模型卸载消息
    更新 AvailableModel 的部署状态
    """
    logger.info(f"Handling model undeployed: model_id={message.model_id}")
    
    async with AsyncSessionLocal() as session:
        try:
            # 更新部署状态
            stmt = (
                update(AvailableModel)
                .where(AvailableModel.id == message.model_id)
                .where(AvailableModel.is_deleted == False)
                .values(
                    is_deployed=False,
                    deployment_id=None,
                    deployment_port=None,
                )
            )
            await session.execute(stmt)
            await session.commit()
            
            logger.info(f"Model {message.model_id} undeployed")
            
        except Exception as e:
            logger.error(f"Failed to update model undeploy status: {e}")
            await session.rollback()
            raise
