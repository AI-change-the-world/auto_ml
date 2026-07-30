"""Logging setup for the sandbox service."""
from __future__ import annotations

import sys

from loguru import logger


_CONFIGURED = False


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    logger.remove()
    logger.configure(extra={"service": "ai_pipeline_sandbox"})
    logger.add(
        sys.stdout,
        level="INFO",
        colorize=False,
        backtrace=False,
        diagnose=False,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {extra[service]} | {name}:{function}:{line} | {message}",
    )
    _CONFIGURED = True
