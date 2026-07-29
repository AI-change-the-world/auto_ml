"""Structured errors emitted by the batch execution runtime."""
from __future__ import annotations

from typing import Any


class RuntimeExecutionError(RuntimeError):
    def __init__(self, message: str, error_detail: dict[str, Any]) -> None:
        super().__init__(message)
        self.error_detail = error_detail
