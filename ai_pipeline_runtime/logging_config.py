from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from loguru import logger

_CONFIGURED = False


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def configure_logging(service_name: str = "ai_pipeline_runtime") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = os.getenv("AI_PIPELINE_RUNTIME_LOG_LEVEL", os.getenv("LOG_LEVEL", "INFO")).upper()
    colorize = os.getenv("AI_PIPELINE_RUNTIME_COLOR_LOGS", "true").lower() == "true"
    logs_dir = Path(os.getenv("AI_PIPELINE_RUNTIME_LOG_DIR", "logs"))
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"{service_name}.log"

    logger.remove()
    logger.configure(extra={"service": service_name})
    logger.add(
        sys.stdout,
        level=level_name,
        colorize=colorize,
        backtrace=False,
        diagnose=False,
        enqueue=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<magenta>{extra[service]}</magenta> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )
    logger.add(
        log_file,
        level=level_name,
        rotation="10 MB",
        retention=5,
        encoding="utf-8",
        backtrace=False,
        diagnose=False,
        enqueue=False,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[service]} | "
            "{name}:{function}:{line} - {message}"
        ),
    )

    intercept_handler = InterceptHandler()
    logging.basicConfig(handlers=[intercept_handler], level=0, force=True)
    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "httpx",
        "pika",
        "urllib3",
        "asyncio",
    ):
        target_logger = logging.getLogger(logger_name)
        target_logger.handlers = [intercept_handler]
        target_logger.propagate = False

    logging.captureWarnings(True)
    _CONFIGURED = True
