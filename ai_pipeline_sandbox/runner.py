"""Small batch-specific runner following the existing sandbox runner contract."""
from __future__ import annotations

import asyncio
import importlib.util
import inspect
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Callable


RESULT_PREFIX = "__AUTO_ML_BATCH_RESULT__="
EVENT_PREFIX = "__AUTO_ML_BATCH_EVENT__="
LOG_PREFIX = "__AUTO_ML_BATCH_LOG__="


def load_module(script_path: Path):
    script_dir = str(script_path.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(f"batch_script_{script_path.stem}", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load script: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def maybe_await(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value


def report(**event: Any) -> None:
    print(EVENT_PREFIX + json.dumps(event, ensure_ascii=False), flush=True)


async def run() -> int:
    if len(sys.argv) != 3:
        print(RESULT_PREFIX + json.dumps({"success": False, "error": "Usage: runner.py <script.py> <payload.json>"}))
        return 2
    try:
        script_path = Path(sys.argv[1]).resolve()
        payload = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        module = load_module(script_path)
        execute_batch = getattr(module, "execute_batch", None)
        if not callable(execute_batch):
            raise RuntimeError("Batch script must define callable execute_batch(params, report)")
        signature = inspect.signature(execute_batch)
        if len(signature.parameters) >= 2:
            result = await maybe_await(execute_batch(payload, report))
        else:
            result = await maybe_await(execute_batch(payload))
        print(RESULT_PREFIX + json.dumps({"success": True, "data": result}, ensure_ascii=False), flush=True)
        return 0
    except Exception as exc:
        error_detail = {
            "source": "batch_script",
            "stage": "execute_batch",
            "exception_type": exc.__class__.__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        print(
            LOG_PREFIX + json.dumps(
                {
                    "level": "error",
                    "message": "batch script crashed",
                    "error_detail": error_detail,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        print(
            RESULT_PREFIX + json.dumps(
                {
                    "success": False,
                    "error": f"{exc.__class__.__name__}: {exc}",
                    "error_detail": error_detail,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
