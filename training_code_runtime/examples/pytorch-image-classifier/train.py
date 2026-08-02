"""Illustrative entrypoint only; the runtime that invokes it is not implemented yet."""
from __future__ import annotations

from typing import Any, Callable


def train(context: dict[str, Any], report: Callable[..., None]) -> dict[str, Any]:
    """Future package entrypoint: write artifacts below context['workspace']['output_dir']."""
    report(event_type="phase", phase="prepare", message="example package started")
    raise NotImplementedError("This example defines the contract but is not executable yet")
