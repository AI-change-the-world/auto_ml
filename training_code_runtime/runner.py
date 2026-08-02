"""Dormant package runner based on the sandbox's line-oriented runner pattern.

This file is not reachable from the HTTP service and is not wired to MQ. It is
tested directly so the package entrypoint and event protocol are stable before
controlled execution is enabled.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import inspect
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from contracts import (
    EVENT_PROTOCOL_VERSION,
    RESULT_PROTOCOL_VERSION,
    ArtifactResult,
    TrainingError,
    TrainingPackageCompletion,
    TrainingResult,
    training_event_adapter,
)
from runtime.protocol import EVENT_PREFIX, LOG_PREFIX, RESULT_PREFIX


RESULT_FILE_NAME = "result.json"


class TrainingRunnerError(RuntimeError):
    """The package did not meet the runner entrypoint or output contract."""


def load_module(script_path: Path) -> Any:
    script_dir = str(script_path.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    module_name = f"training_package_{script_path.stem}_{hashlib.sha256(str(script_path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise TrainingRunnerError(f"unable to load training entrypoint: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def maybe_await(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value


async def run() -> int:
    if len(sys.argv) != 3:
        _emit_result({"success": False, "error": "Usage: runner.py <entrypoint.py> <execution.json>"})
        return 2

    context: dict[str, Any] | None = None
    output_dir: Path | None = None
    try:
        script_path = Path(sys.argv[1]).resolve(strict=True)
        context = _load_context(Path(sys.argv[2]))
        execution_id = _required_text(context, "execution_id")
        output_dir = _output_dir(context)
        output_dir.mkdir(parents=True, exist_ok=True)

        module = load_module(script_path)
        train = getattr(module, "train", None)
        _validate_train_entrypoint(train)
        sequence = 0

        def report(**payload: Any) -> None:
            nonlocal sequence
            _reject_runner_owned_event_fields(payload)
            event = {
                "protocol_version": EVENT_PROTOCOL_VERSION,
                "execution_id": execution_id,
                "sequence": sequence,
                "occurred_at": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
                **payload,
            }
            try:
                validated = training_event_adapter.validate_python(event)
            except ValidationError as exc:
                raise TrainingRunnerError(f"invalid training event: {exc}") from exc
            _emit_event(validated.model_dump(mode="json"))
            sequence += 1

        completion = TrainingPackageCompletion.model_validate(
            await maybe_await(train(context, report))
        )
        result = _build_success_result(execution_id, completion, output_dir)
        _write_result(output_dir, result)
        _emit_result(result.model_dump(mode="json"))
        return 0
    except Exception as exc:
        diagnostic = {
            "source": "training_code_runner",
            "stage": "run_training_code",
            "exception_type": exc.__class__.__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        _emit_log({"level": "error", "message": "training package crashed", "error_detail": diagnostic})
        execution_id = str((context or {}).get("execution_id") or "unknown")
        result = TrainingResult(
            protocol_version=RESULT_PROTOCOL_VERSION,
            execution_id=execution_id,
            status="failed",
            error=TrainingError(
                stage="run_training_code",
                error_type=exc.__class__.__name__,
                message=str(exc) or exc.__class__.__name__,
            ),
        ) if _is_uuid(execution_id) else None
        if result is not None:
            if output_dir is not None:
                _write_result(output_dir, result)
            _emit_result(result.model_dump(mode="json"))
        else:
            _emit_result({"success": False, "error": f"{exc.__class__.__name__}: {exc}", "error_detail": diagnostic})
        return 1


def _load_context(context_path: Path) -> dict[str, Any]:
    try:
        value = json.loads(context_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TrainingRunnerError(f"unable to load execution context: {exc}") from exc
    if not isinstance(value, dict):
        raise TrainingRunnerError("execution context must be a JSON object")
    return value


def _required_text(context: dict[str, Any], key: str) -> str:
    value = context.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TrainingRunnerError(f"execution context requires non-empty `{key}`")
    return value


def _output_dir(context: dict[str, Any]) -> Path:
    workspace = context.get("workspace")
    if not isinstance(workspace, dict):
        raise TrainingRunnerError("execution context requires a workspace object")
    value = workspace.get("output_dir")
    if not isinstance(value, str) or not value.strip():
        raise TrainingRunnerError("execution context requires workspace.output_dir")
    return Path(value).resolve()


def _validate_train_entrypoint(train: Any) -> Callable[[dict[str, Any], Callable[..., None]], Any]:
    if not callable(train):
        raise TrainingRunnerError("training package must define callable train(context, report)")
    if len(inspect.signature(train).parameters) != 2:
        raise TrainingRunnerError("train must accept exactly two parameters: context and report")
    return train


def _reject_runner_owned_event_fields(payload: dict[str, Any]) -> None:
    protected = {"protocol_version", "execution_id", "sequence", "occurred_at"}
    supplied = protected.intersection(payload)
    if supplied:
        raise TrainingRunnerError(
            "report must not set runner-owned fields: " + ", ".join(sorted(supplied))
        )


def _build_success_result(
    execution_id: str,
    completion: TrainingPackageCompletion,
    output_dir: Path,
) -> TrainingResult:
    artifacts: list[ArtifactResult] = []
    for artifact in completion.artifacts:
        artifact_path = (output_dir / artifact.path).resolve()
        try:
            artifact_path.relative_to(output_dir)
        except ValueError as exc:
            raise TrainingRunnerError(f"artifact path escapes output directory: {artifact.path}") from exc
        if not artifact_path.is_file():
            raise TrainingRunnerError(f"declared artifact does not exist: {artifact.path}")
        artifacts.append(
            ArtifactResult(
                path=artifact.path,
                role=artifact.role,
                format=artifact.format,
                size_bytes=artifact_path.stat().st_size,
                sha256=_file_sha256(artifact_path),
                deployable=artifact.deployable,
                metadata=artifact.metadata,
            )
        )
    return TrainingResult(
        protocol_version=RESULT_PROTOCOL_VERSION,
        execution_id=execution_id,
        status="succeeded",
        summary=completion.summary,
        metrics=completion.metrics,
        artifacts=artifacts,
        model=completion.model,
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_result(output_dir: Path, result: TrainingResult) -> None:
    (output_dir / RESULT_FILE_NAME).write_text(
        result.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )


def _emit_event(event: dict[str, Any]) -> None:
    print(EVENT_PREFIX + json.dumps(event, ensure_ascii=False, allow_nan=False), flush=True)


def _emit_log(event: dict[str, Any]) -> None:
    print(LOG_PREFIX + json.dumps(event, ensure_ascii=False, allow_nan=False), flush=True)


def _emit_result(result: dict[str, Any]) -> None:
    print(RESULT_PREFIX + json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)


def _is_uuid(value: str) -> bool:
    try:
        from uuid import UUID

        UUID(value)
        return True
    except (TypeError, ValueError):
        return False


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
