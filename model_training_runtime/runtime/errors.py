"""Structured errors for the training-code runtime foundation."""
from __future__ import annotations

from typing import Any


class RuntimeExecutionError(RuntimeError):
    """An operational failure with safe, machine-readable diagnostics."""

    def __init__(self, message: str, error_detail: dict[str, Any]) -> None:
        super().__init__(message)
        self.error_detail = error_detail
