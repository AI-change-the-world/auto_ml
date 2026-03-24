"""
心跳检查定时任务
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.config.settings import get_settings
from app.utils.http_client import get_http_client

settings = get_settings()
scheduler = AsyncIOScheduler()


async def check_ai_platform_health():
    """检查 AI Platform 服务健康状态"""
    try:
        client = get_http_client()
        is_healthy = await client.health_check()

        if is_healthy:
            logger.debug("AI Platform health check: OK")
        else:
            logger.warning(
                "AI Platform health check: FAILED - Service may be unavailable")

    except Exception as e:
        logger.error(f"AI Platform health check error: {e}")


def start_scheduler():
    """启动定时任务调度器"""
    # 添加心跳检查任务
    scheduler.add_job(
        check_ai_platform_health,
        "interval",
        seconds=settings.heartbeat_interval,
        id="ai_platform_health_check",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started, heartbeat interval: {settings.heartbeat_interval}s")


def stop_scheduler():
    """停止调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
