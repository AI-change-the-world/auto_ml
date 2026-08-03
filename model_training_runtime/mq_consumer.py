"""RabbitMQ consumer owned by the model training runtime service."""
from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pika
from pika.exceptions import ProbableAuthenticationError
from pydantic import ValidationError

from artifacts import PersistedArtifact, persist_execution_artifacts
from contracts import TrainingCodeSubmission
from coordinator import ExecutionCoordinator, ExecutionCoordinatorError
from execution_policy import ExecutionPolicyError, validate_execution_policy
from runtime import (
    ManagedRuntimeSpec,
    RuntimeExecutionSettings,
    ServiceSubprocessExecutor,
    TrainingRuntimeManager,
)
from storage import (
    OpenDalS3Storage,
    load_model_training_runtime_config,
    load_platform_config,
)
from runtime.logging_utils import logger


SERVICE_NAME = "model-training-runtime"
TASK_PENDING = 0
TASK_RUNNING = 1
TASK_COMPLETED = 3
TASK_FAILED = 4


def _section(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _configured_value(
    sections: tuple[dict[str, Any], ...],
    key: str,
    environment_name: str,
    fallback: str,
) -> str:
    for section in sections:
        value = section.get(key)
        if value is not None and value != "":
            return str(value)
    return os.getenv(environment_name, fallback)


def _queue_or_routing_value(
    runtime_mq: dict[str, Any],
    shared_mq: dict[str, Any],
    section_name: str,
    key: str,
    flat_key: str,
    environment_name: str,
    fallback: str,
) -> str:
    for mq in (runtime_mq, shared_mq):
        nested = _section(mq, section_name)
        value = nested.get(key)
        if value is not None and value != "":
            return str(value)
        value = mq.get(flat_key)
        if value is not None and value != "":
            return str(value)
    return os.getenv(environment_name, fallback)


class TrainingCodeConsumer:
    """Consumes only ``training.code.execute`` for the running Runtime API."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._connection: pika.BlockingConnection | None = None
        self._channel = None
        self._active_lock = threading.Lock()
        self._active_executions = 0

    @property
    def active_executions(self) -> int:
        with self._active_lock:
            return self._active_executions

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    @property
    def is_connected(self) -> bool:
        return bool(
            self._connection
            and not self._connection.is_closed
            and self._channel
            and not self._channel.is_closed
        )

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._consume_loop,
            name="model-training-runtime-mq-consumer",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=5)
        if not thread or not thread.is_alive():
            self._thread = None

    def _settings(self) -> dict[str, Any]:
        platform_config = load_platform_config()
        runtime_config = _section(platform_config, "model-training-runtime") or _section(
            platform_config,
            "training-code-runtime",
        )
        runtime_mq = _section(runtime_config, "rabbitmq")
        mq = _section(platform_config, "rabbitmq")
        return {
            "host": _configured_value((runtime_mq, mq), "host", "RABBITMQ_HOST", "localhost"),
            "port": int(_configured_value((runtime_mq, mq), "port", "RABBITMQ_PORT", "5672")),
            "username": _configured_value((runtime_mq, mq), "username", "RABBITMQ_USER", "guest"),
            "password": _configured_value((runtime_mq, mq), "password", "RABBITMQ_PASSWORD", "guest"),
            "virtual_host": _configured_value((runtime_mq, mq), "virtual_host", "RABBITMQ_VHOST", "/"),
            "exchange": _configured_value((runtime_mq, mq), "exchange_name", "RABBITMQ_EXCHANGE", "auto_ml_exchange"),
            "exchange_type": _configured_value((runtime_mq, mq), "exchange_type", "RABBITMQ_EXCHANGE_TYPE", "topic"),
            "execute_queue": _queue_or_routing_value(
                runtime_mq,
                mq,
                "queues",
                "training_code_execute",
                "training_code_execute_queue",
                "TRAINING_CODE_EXECUTE_QUEUE",
                "training.code.execute",
            ),
            "execute_routing_key": _queue_or_routing_value(
                runtime_mq,
                mq,
                "routing_keys",
                "training_code_execute",
                "training_code_execute_routing_key",
                "TRAINING_CODE_EXECUTE_ROUTING_KEY",
                "training.code.execute",
            ),
            "task_status_routing_key": _queue_or_routing_value(
                runtime_mq,
                mq,
                "routing_keys",
                "task_status",
                "task_status_routing_key",
                "TASK_STATUS_ROUTING_KEY",
                "task.status.update",
            ),
            "task_log_routing_key": _queue_or_routing_value(
                runtime_mq,
                mq,
                "routing_keys",
                "task_log",
                "task_log_routing_key",
                "TASK_LOG_ROUTING_KEY",
                "task.log",
            ),
            "model_registered_routing_key": _queue_or_routing_value(
                runtime_mq,
                mq,
                "routing_keys",
                "model_registered",
                "model_registered_routing_key",
                "MODEL_REGISTERED_ROUTING_KEY",
                "model.registered",
            ),
        }

    def _connect(self):
        settings = self._settings()
        credentials = pika.PlainCredentials(settings["username"], settings["password"])
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings["host"],
                    port=settings["port"],
                    virtual_host=settings["virtual_host"],
                    credentials=credentials,
                    heartbeat=60,
                    blocked_connection_timeout=300,
                )
            )
        except ProbableAuthenticationError as exc:
            raise RuntimeError(
                "RabbitMQ authentication was refused for "
                f"host={settings['host']} port={settings['port']} "
                f"username={settings['username']} vhost={settings['virtual_host']}; "
                "check the shared Nacos `rabbitmq` configuration or RABBITMQ_* environment variables"
            ) from exc
        channel = connection.channel()
        channel.exchange_declare(
            exchange=settings["exchange"],
            exchange_type=settings["exchange_type"],
            durable=True,
        )
        channel.queue_declare(queue=settings["execute_queue"], durable=True)
        channel.queue_bind(
            queue=settings["execute_queue"],
            exchange=settings["exchange"],
            routing_key=settings["execute_routing_key"],
        )
        channel.basic_qos(prefetch_count=1)
        return connection, channel, settings

    def _consume_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                connection, channel, settings = self._connect()
                self._connection = connection
                self._channel = channel
                channel.basic_consume(
                    queue=settings["execute_queue"],
                    on_message_callback=self._on_message,
                    auto_ack=False,
                )
                logger.info("Training code consumer is consuming queue=%s", settings["execute_queue"])
                while not self._stop_event.is_set():
                    connection.process_data_events(time_limit=1)
            except Exception:
                if not self._stop_event.is_set():
                    logger.warning("Training code consumer connection failed; retrying", exc_info=True)
                    time.sleep(2)
            finally:
                self._close()

    def _close(self) -> None:
        channel, connection = self._channel, self._connection
        self._channel = None
        self._connection = None
        if channel and not channel.is_closed:
            try:
                channel.close()
            except Exception:
                pass
        if connection and not connection.is_closed:
            try:
                connection.close()
            except Exception:
                pass

    def _on_message(self, channel, method, _properties, body: bytes) -> None:
        payload: dict[str, Any] = {}
        try:
            payload = json.loads(body)
            submission = TrainingCodeSubmission.model_validate(payload)
            validate_execution_policy(submission, load_model_training_runtime_config())
            task_id = submission.task.task_id
            with self._active_lock:
                self._active_executions += 1
            self._publish_status(
                task_id,
                TASK_RUNNING,
                "custom training script started",
                extra_data=_execution_extra_data(submission),
            )
            outcome = asyncio.run(self._execute(submission))
            self._publish_logs(task_id, outcome.logs)
            self._publish_events(task_id, outcome.events)
            self._publish_status(
                task_id,
                TASK_COMPLETED if outcome.result.status == "succeeded" else TASK_FAILED,
                outcome.result.summary or _result_message(outcome.result.model_dump(mode="json")),
                extra_data={
                    "backend": "training_code_runtime",
                    "execution_id": str(submission.execution_id),
                    "result": outcome.result.model_dump(mode="json"),
                    "artifacts": [_artifact_payload(item) for item in outcome.artifacts],
                },
            )
            if outcome.result.status == "succeeded":
                self._publish_deployable_model(task_id, submission, outcome)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except (
            json.JSONDecodeError,
            ValidationError,
            ExecutionCoordinatorError,
            ExecutionPolicyError,
            RuntimeError,
        ) as exc:
            task_id = _task_id_from_payload(payload)
            logger.error("Custom training execution failed: task_id=%s", task_id, exc_info=True)
            if task_id is not None:
                self._publish_status(
                    task_id,
                    TASK_FAILED,
                    str(exc)[:8000],
                    extra_data=_execution_extra_data_from_payload(payload),
                )
                self._publish_log(task_id, f"[runtime] {exc}", "ERROR")
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            logger.exception("Unexpected custom training consumer failure")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            with self._active_lock:
                self._active_executions = max(0, self._active_executions - 1)

    async def _execute(self, submission: TrainingCodeSubmission) -> "WorkerExecutionOutcome":
        coordinator, workspace_root = _build_coordinator()
        try:
            outcome = await coordinator.execute(submission)
            artifacts = await persist_execution_artifacts(coordinator.storage, outcome)
            return WorkerExecutionOutcome(
                result=outcome.result,
                events=outcome.events,
                logs=outcome.logs,
                artifacts=artifacts,
            )
        finally:
            import shutil

            shutil.rmtree(workspace_root / str(submission.execution_id), ignore_errors=True)

    def _publish_status(
        self,
        task_id: int,
        status: int,
        message: str | None = None,
        *,
        extra_data: dict[str, Any] | None = None,
    ) -> None:
        self._publish(
            self._settings()["task_status_routing_key"],
            {
                "message_type": "task.status.update",
                "service_name": SERVICE_NAME,
                "timestamp": _timestamp(),
                "task_id": task_id,
                "status": status,
                "message": message,
                "extra_data": extra_data,
            },
        )

    def _publish_logs(self, task_id: int, logs: tuple[dict[str, Any], ...]) -> None:
        for payload in logs:
            self._publish_log(
                task_id,
                str(payload.get("message") or "training runtime log"),
                str(payload.get("level") or "INFO").upper(),
            )

    def _publish_events(self, task_id: int, events: tuple[dict[str, Any], ...]) -> None:
        for event in events:
            if event.get("event_type") == "metric":
                metrics = event.get("metrics") or {}
                self._publish_log(task_id, f"[metric] {json.dumps(metrics, ensure_ascii=False, sort_keys=True)}")
            elif event.get("event_type") == "phase":
                self._publish_log(task_id, f"[{event.get('phase', 'phase')}] {event.get('message') or ''}".strip())

    def _publish_log(self, task_id: int, content: str, level: str = "INFO") -> None:
        self._publish(
            self._settings()["task_log_routing_key"],
            {
                "message_type": "task.log",
                "service_name": SERVICE_NAME,
                "timestamp": _timestamp(),
                "task_id": task_id,
                "log_content": content[:16000],
                "log_level": level if level in {"DEBUG", "INFO", "WARNING", "ERROR"} else "INFO",
            },
        )

    def _publish_deployable_model(
        self,
        task_id: int,
        submission: TrainingCodeSubmission,
        outcome: "WorkerExecutionOutcome",
    ) -> None:
        selected = next(
            (
                item
                for item in outcome.artifacts
                if item.artifact.deployable
                and item.artifact.role.value == "model"
                and item.artifact.format == "onnx"
            ),
            None,
        )
        if selected is None or outcome.result.model is None:
            return
        runtime_template = _runtime_template(outcome.result.model)
        if runtime_template is None:
            self._publish_log(
                task_id,
                "[artifact] deployable ONNX was stored but its task kind has no compatible inference template",
                "WARNING",
            )
            return
        checkpoint = next((item for item in outcome.artifacts if item.artifact.role.value == "checkpoint"), None)
        metrics = outcome.result.metrics
        loss = next((value for key, value in metrics.items() if "loss" in key.lower()), None)
        model_info = {
            "onnx_save_path": selected.object.object_key,
            "save_path": checkpoint.object.object_key if checkpoint is not None else None,
            "task_kind": outcome.result.model.task_kind,
            "class_names": outcome.result.model.class_names,
            "trained_model_name": f"{submission.package.key}-task-{task_id}",
            "loss": loss,
            "runtime_template": runtime_template,
            "execution_id": str(submission.execution_id),
        }
        self._publish(
            self._settings()["model_registered_routing_key"],
            {
                "message_type": "model.registered",
                "service_name": SERVICE_NAME,
                "timestamp": _timestamp(),
                "task_id": task_id,
                "model_info": model_info,
            },
        )

    def _publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        channel = self._channel
        if channel is None or channel.is_closed:
            raise RuntimeError("RabbitMQ channel is unavailable")
        settings = self._settings()
        channel.basic_publish(
            exchange=settings["exchange"],
            routing_key=routing_key,
            body=json.dumps(payload, ensure_ascii=False, allow_nan=False),
            properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
            mandatory=True,
        )


class WorkerExecutionOutcome:
    def __init__(
        self,
        *,
        result,
        events: tuple[dict[str, Any], ...],
        logs: tuple[dict[str, Any], ...],
        artifacts: tuple[PersistedArtifact, ...],
    ) -> None:
        self.result = result
        self.events = events
        self.logs = logs
        self.artifacts = artifacts


def _build_coordinator() -> tuple[ExecutionCoordinator, Path]:
    config = load_model_training_runtime_config()
    execution = config.get("execution") if isinstance(config.get("execution"), dict) else {}
    if execution.get("enabled") is not True:
        raise RuntimeError("model-training-runtime.execution.enabled is false")
    runtime_ids = execution.get(
        "runtime_ids",
        ["ultralytics-8.3.0-pytorch-2.5-cu124", "pytorch-2.5-cu124"],
    )
    if isinstance(runtime_ids, str):
        runtime_ids = [runtime_ids]
    if not isinstance(runtime_ids, list) or not runtime_ids:
        raise RuntimeError("model-training-runtime.execution.runtime_ids is invalid")
    import sys
    import tempfile

    python_executable = Path(str(execution.get("python_executable") or sys.executable)).resolve()
    workspace_root = Path(str(execution.get("workspace_root") or (Path(tempfile.gettempdir()) / "model-training-runtime" / "workspaces"))).resolve()
    settings = RuntimeExecutionSettings(
        workspace_root=workspace_root,
        idle_timeout_seconds=int(execution.get("idle_timeout_seconds", 180)),
        max_output_bytes=int(execution.get("max_output_bytes", 2 * 1024 * 1024)),
        max_processes=int(execution.get("max_processes", 32)),
        process_fsize_bytes=int(execution.get("process_fsize_bytes", 50 * 1024 * 1024)),
        process_nofile=int(execution.get("process_nofile", 512)),
    )
    runtimes = [ManagedRuntimeSpec(runtime_id=str(runtime_id), python_executable=python_executable) for runtime_id in runtime_ids]
    return (
        ExecutionCoordinator(
            OpenDalS3Storage(),
            TrainingRuntimeManager(settings, runtimes),
            executor=ServiceSubprocessExecutor(),
        ),
        workspace_root,
    )


def _artifact_payload(item: PersistedArtifact) -> dict[str, Any]:
    return {"artifact": item.artifact.model_dump(mode="json"), "object": item.object.model_dump(mode="json")}


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _task_id_from_payload(payload: dict[str, Any]) -> int | None:
    task = payload.get("task")
    value = task.get("task_id") if isinstance(task, dict) else None
    return value if isinstance(value, int) and value > 0 else None


def _execution_extra_data(submission: TrainingCodeSubmission) -> dict[str, str]:
    return {
        "backend": "training_code_runtime",
        "execution_id": str(submission.execution_id),
    }


def _execution_extra_data_from_payload(payload: dict[str, Any]) -> dict[str, str]:
    result = {"backend": "training_code_runtime"}
    execution_id = payload.get("execution_id")
    if isinstance(execution_id, str) and execution_id:
        result["execution_id"] = execution_id
    return result


def _result_message(result: dict[str, Any]) -> str:
    error = result.get("error")
    return str(error.get("message") if isinstance(error, dict) else "custom training failed")


def _runtime_template(model) -> str | None:
    task_kind = model.task_kind
    framework_id = model.framework.id
    if task_kind in {"detection", "detection_bbox", "detection_obb"}:
        return "ultralytics_detection"
    if task_kind == "classification":
        return "ultralytics_classification" if framework_id == "ultralytics" else "onnx_classification"
    return None
