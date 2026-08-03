"""Optional Linux resource-limit command construction for task workers."""
from __future__ import annotations

import os
import shutil

from .logging_utils import logger
from .models import RuntimeExecutionSettings


def build_resource_limit_command(
    settings: RuntimeExecutionSettings,
    *,
    memory_bytes: int,
    cpu_seconds: int,
) -> list[str] | None:
    """Build a `prlimit ... --` prefix when the platform supports it.

    Container- or Job-level quotas remain the primary isolation boundary. This
    optional inner-process limit is defense in depth and degrades safely when
    `prlimit` is unavailable.
    """
    if os.name != "posix":
        return None
    prlimit = shutil.which("prlimit")
    if not prlimit:
        logger.warning("prlimit is unavailable; training subprocess limits are disabled")
        return None
    limits = [
        ("--nproc", settings.max_processes),
        ("--cpu", cpu_seconds),
        ("--as", memory_bytes),
        ("--fsize", settings.process_fsize_bytes),
        ("--nofile", settings.process_nofile),
    ]
    return [prlimit, *(f"{name}={value}" for name, value in limits if value > 0), "--"]
