"""
数据库配置
使用 SQLAlchemy 2.0 AsyncIO
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger

from .settings import get_settings

# 创建异步引擎
settings = get_settings()
engine = create_async_engine(
    settings.database.url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 声明基类
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（用于依赖注入）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库（仅创建缺失表，不做自动结构迁移）"""
    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册
        from app.db.models import (
            Dataset, Asset, SampleItem, Annotation, AnnotationRecord,
            AnnotationCollaborator, AnnotationSampleAssignment,
            Task, TaskLog, TaskSource, BaseModels,
            AvailableModel, ModelInferenceLog,
            AiPipelineTemplate, AiPipelineTemplateVersion, AiPipelineBinding, AiPipelineProviderResource,
            AiPipelineRun, AiPipelineRunStep, AiPipelineArtifact, AiPipelineEventLog,
            AiPipelineBatchRun, AiPipelineBatchRunItem, AiPipelineBatchRunEvent,
            AiPipelineBatchBuiltinScriptSetting,
        )
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        logger.info(
            "Database tables ensured successfully. "
            "Schema/data changes for existing MySQL databases must be applied via SQL scripts in mysql/."
        )
