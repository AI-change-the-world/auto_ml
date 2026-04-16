"""
AutoML Server - FastAPI 主入口
"""
import os
import time
from app.modules.home import router as home_router
from app.modules.deploy import router as deploy_router
from app.modules.task import router as task_router
from app.modules.annotation import router as annotation_router
from app.modules.dataset import router as dataset_router
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.common import Result
from app.common.exceptions import AppException
from app.config.nacos_config_center import get_config_center
from app.config.settings import get_settings
from app.mq.consumer import get_consumer
from app.mq.publisher import get_publisher
from app.mq.messages import MessageType
from app.mq.handlers import (
    handle_task_status_update,
    handle_task_log,
    handle_model_registered,
    handle_model_deployed,
    handle_model_undeployed,
)

settings = get_settings()


def _init_mq_with_retry(loop: asyncio.AbstractEventLoop):
    retries = max(1, int(os.getenv("MQ_STARTUP_RETRIES", "12")))
    interval = max(1, int(os.getenv("MQ_STARTUP_RETRY_INTERVAL", "5")))
    ready_timeout = max(1, int(os.getenv("MQ_STARTUP_READY_TIMEOUT", "5")))
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            consumer = get_consumer()

            consumer.register_handler(
                MessageType.TASK_STATUS_UPDATE.value,
                handle_task_status_update,
                is_async=True
            )
            consumer.register_handler(
                MessageType.TASK_LOG.value,
                handle_task_log,
                is_async=True
            )
            consumer.register_handler(
                MessageType.MODEL_REGISTERED.value,
                handle_model_registered,
                is_async=True
            )
            consumer.register_handler(
                MessageType.MODEL_DEPLOYED.value,
                handle_model_deployed,
                is_async=True
            )
            consumer.register_handler(
                MessageType.MODEL_UNDEPLOYED.value,
                handle_model_undeployed,
                is_async=True
            )

            consumer.start(event_loop=loop)
            if not consumer.wait_until_ready(timeout=ready_timeout):
                raise RuntimeError(
                    consumer.last_error
                    or f"consumer not ready within {ready_timeout}s"
                )
            publisher = get_publisher()
            if not publisher.wait_until_ready(timeout=ready_timeout):
                raise RuntimeError("publisher connection is not ready")
            logger.info(
                f"RabbitMQ startup completed on attempt {attempt}/{retries}"
            )
            return
        except Exception as e:
            last_error = e
            logger.warning(
                f"RabbitMQ startup attempt {attempt}/{retries} failed: {e}"
            )
            if attempt < retries:
                time.sleep(interval)

    raise RuntimeError(
        f"Failed to start MQ after {retries} attempts: {last_error}"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    get_config_center().start()

    # 初始化数据库（自动建表）
    from app.config.database import init_db
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Failed to init database: {e}")

    # 初始化 S3 bucket
    from app.utils.s3_delegate import get_s3_delegate
    try:
        s3 = get_s3_delegate()
        await s3.ensure_buckets()
    except Exception as e:
        logger.error(f"Failed to ensure S3 buckets: {e}")

    # 启动消息消费者
    try:
        loop = asyncio.get_event_loop()
        _init_mq_with_retry(loop)
        logger.info("RabbitMQ consumer started")
    except Exception as e:
        logger.error(f"Failed to start MQ consumer: {e}")
        get_config_center().stop()
        raise

    yield

    # 关闭
    logger.info("Shutting down...")
    try:
        consumer = get_consumer()
        consumer.stop()
    except Exception:
        pass
    try:
        publisher = get_publisher()
        publisher.close()
    except Exception:
        pass
    get_config_center().stop()


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/swagger-ui",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=200,  # 业务异常返回 200，通过 code 区分
        content=Result.fail(code=exc.code, message=exc.message,
                            data=exc.data).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=Result.fail(code=500, message=str(exc)
                            ).model_dump(mode="json"),
    )


# 健康检查
@app.get("/health", tags=["健康检查"])
async def health_check():
    return {"status": "ok", "service": settings.app_name}


# 注册路由

app.include_router(dataset_router)
app.include_router(annotation_router)
app.include_router(task_router)
app.include_router(deploy_router)
app.include_router(home_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
