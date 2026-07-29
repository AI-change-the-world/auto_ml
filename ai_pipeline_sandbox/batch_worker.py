"""RabbitMQ consumer that executes platform batch scripts in isolated subprocesses."""
from __future__ import annotations

import asyncio
from collections import deque
import json
import logging
import os
import queue
import shutil
import threading
import time
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

import pika

from config import SandboxSettings
from runtime import (
    RuntimeProcessError,
    ScriptEnvironmentError,
    ScriptEnvironmentManager,
    extract_script_package,
    load_package_environment,
    run_isolated_process,
)
from storage import DatasetStorage


logger = logging.getLogger(__name__)

EVENT_PREFIX = "__AUTO_ML_BATCH_EVENT__="
RESULT_PREFIX = "__AUTO_ML_BATCH_RESULT__="
LOG_PREFIX = "__AUTO_ML_BATCH_LOG__="
SCRIPT_DIAGNOSTIC_MAX_CHARS = 4096
SCRIPT_DIAGNOSTIC_MAX_LINES = 40


class SandboxScriptExecutionError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        error_detail: dict[str, Any] | None = None,
        output_tail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.error_detail = error_detail or {}
        self.output_tail = output_tail


class BatchSandboxWorker:
    def __init__(self, settings: SandboxSettings) -> None:
        self.settings = settings
        self.storage = DatasetStorage(settings.storage)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._connection: pika.BlockingConnection | None = None
        self._channel = None
        self._active_lock = threading.Lock()
        self._active_chunks = 0

    @property
    def active_chunks(self) -> int:
        with self._active_lock:
            return self._active_chunks

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
        self.settings.workspace_root.mkdir(parents=True, exist_ok=True)
        self.settings.script_runtime.venv_root.mkdir(parents=True, exist_ok=True)
        self.settings.script_runtime.pip_cache_dir.mkdir(parents=True, exist_ok=True)
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._consume_loop, name="pipeline-sandbox-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._thread = None

    def update_execution_limits(self, settings: SandboxSettings) -> None:
        self.settings = replace(
            self.settings,
            timeout_seconds=settings.timeout_seconds,
            max_output_bytes=settings.max_output_bytes,
            memory_bytes=settings.memory_bytes,
            cpu_seconds=settings.cpu_seconds,
            max_processes=settings.max_processes,
            script_runtime=settings.script_runtime,
        )
    def _connect(self):
        mq = self.settings.rabbitmq
        credentials = pika.PlainCredentials(mq.username, mq.password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=mq.host,
                port=mq.port,
                virtual_host=mq.virtual_host,
                credentials=credentials,
                heartbeat=60,
                blocked_connection_timeout=300,
            )
        )
        channel = connection.channel()
        channel.exchange_declare(exchange=mq.exchange_name, exchange_type=mq.exchange_type, durable=True)
        channel.queue_declare(queue=mq.execute_queue, durable=True)
        channel.queue_bind(queue=mq.execute_queue, exchange=mq.exchange_name, routing_key=mq.execute_routing_key)
        channel.basic_qos(prefetch_count=1)
        return connection, channel

    def _consume_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                connection, channel = self._connect()
                self._connection = connection
                self._channel = channel
                channel.basic_consume(queue=self.settings.rabbitmq.execute_queue, on_message_callback=self._on_message, auto_ack=False)
                while not self._stop_event.is_set():
                    connection.process_data_events(time_limit=1)
            except Exception:
                if not self._stop_event.is_set():
                    logger.warning("Sandbox worker RabbitMQ connection failed; retrying", exc_info=True)
                    time.sleep(2)
            finally:
                self._close()

    def _on_message(self, channel, method, _properties, body: bytes) -> None:
        payload: dict[str, Any] = {}
        try:
            payload = json.loads(body)
            if payload.get("message_type") != "pipeline.batch.execute":
                channel.basic_ack(delivery_tag=method.delivery_tag)
                return
            with self._active_lock:
                self._active_chunks += 1
            self._execute_payload(payload)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as exc:
            run_id = ""
            chunk_key = ""
            try:
                run_id = str(payload.get("run_id") or "")
                chunk_key = str(payload.get("chunk_key") or "")
            except Exception:
                pass
            logger.exception(
                "Sandbox message handling failed: run_id=%s chunk_key=%s",
                run_id,
                chunk_key,
            )
            if run_id and chunk_key:
                self._publish_result(
                    run_id,
                    chunk_key,
                    self._failed_results(payload, f"sandbox error: {exc}", "message_handling"),
                )
            channel.basic_ack(delivery_tag=method.delivery_tag)
        finally:
            with self._active_lock:
                self._active_chunks = max(0, self._active_chunks - 1)

    def _execute_payload(self, payload: dict[str, Any]) -> None:
        run_id = str(payload["run_id"])
        chunk_key = str(payload["chunk_key"])
        script_key = str(payload["script_key"])
        task_root = self.settings.workspace_root / f"task_{run_id}_{uuid.uuid4().hex}"
        task_root.mkdir(parents=True, exist_ok=False)
        try:
            self._publish_progress(
                run_id,
                chunk_key,
                0,
                len(payload.get("items") or []),
                "sandbox started",
                phase="prepare",
            )
            runnable_items, failed_results = self._prepare_inputs(payload, task_root)
            if runnable_items:
                script_result = self._run_script(payload, runnable_items, task_root)
                results = self._normalize_results(runnable_items, script_result)
            else:
                results = []
            results.extend(failed_results)
            self._publish_result(run_id, chunk_key, results)
        except Exception as exc:
            error_detail = self._execution_error_detail(payload, exc)
            if isinstance(exc, SandboxScriptExecutionError):
                logger.error(
                    "Sandbox chunk execution failed: run_id=%s chunk_key=%s script_key=%s detail=%s",
                    run_id,
                    chunk_key,
                    script_key,
                    error_detail,
                )
            else:
                logger.exception(
                    "Sandbox chunk execution failed: run_id=%s chunk_key=%s script_key=%s",
                    run_id,
                    chunk_key,
                    script_key,
                )
            self._publish_result(
                run_id,
                chunk_key,
                self._failed_results(
                    payload,
                    f"sandbox error: {exc}",
                    "execute_chunk",
                    error_detail=error_detail,
                ),
            )
        finally:
            shutil.rmtree(task_root, ignore_errors=True)

    def _prepare_inputs(
        self,
        payload: dict[str, Any],
        task_root: Path,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        runnable_items: list[dict[str, Any]] = []
        failed_results: list[dict[str, Any]] = []
        items = payload.get("items") if isinstance(payload.get("items"), list) else []
        for raw_item in items:
            if not isinstance(raw_item, dict):
                continue
            batch_item_id = raw_item.get("batch_item_id")
            asset_path = raw_item.get("asset_path")
            if not isinstance(batch_item_id, int) or not isinstance(asset_path, str) or not asset_path:
                failed_results.append({
                    "batch_item_id": batch_item_id,
                    "status": "failed",
                    "error": "sample asset path is unavailable",
                    "error_detail": {
                        "source": "sandbox",
                        "stage": "validate_input",
                        "message": "sample asset path is unavailable",
                    },
                })
                continue
            file_name = str(raw_item.get("asset_file_name") or f"sample_{batch_item_id}")
            destination = task_root / "inputs" / f"{batch_item_id}_{Path(file_name).name}"
            try:
                asyncio.run(self.storage.download(asset_path, destination))
            except Exception as exc:
                logger.exception(
                    "Sandbox input download failed: run_id=%s chunk_key=%s batch_item_id=%s",
                    payload.get("run_id"),
                    payload.get("chunk_key"),
                    batch_item_id,
                )
                failed_results.append({
                    "batch_item_id": batch_item_id,
                    "status": "failed",
                    "error": f"failed to download sample: {exc}",
                    "error_detail": {
                        "source": "sandbox",
                        "stage": "download_dataset_asset",
                        "exception_type": exc.__class__.__name__,
                        "message": str(exc),
                    },
                })
                continue
            item = dict(raw_item)
            item["local_path"] = str(destination)
            runnable_items.append(item)
            self._publish_progress(
                str(payload["run_id"]),
                str(payload["chunk_key"]),
                0,
                len(items),
                "sample input prepared",
                phase="prepare",
            )
        return runnable_items, failed_results

    def _run_script(self, payload: dict[str, Any], items: list[dict[str, Any]], task_root: Path) -> Any:
        script_path, requirements_file, bundle_environment = self._resolve_script_path(payload, task_root)
        self._publish_progress(
            str(payload["run_id"]),
            str(payload["chunk_key"]),
            0,
            len(items),
            "preparing script virtual environment",
            phase="environment",
        )
        environment_manager = ScriptEnvironmentManager(
            self.settings.script_runtime,
            self.settings.timeout_seconds,
            self.settings.max_output_bytes,
            resource_limit_command=self._environment_resource_limit_command(),
            output_callback=lambda stage, message: self._publish_progress(
                str(payload["run_id"]),
                str(payload["chunk_key"]),
                0,
                len(items),
                f"{stage}: {message}"[:512],
                phase="environment",
            ),
        )
        environment = environment_manager.prepare(
            task_root=task_root,
            script_key=str(payload["script_key"]),
            script_version=str(payload.get("script_version") or "unknown"),
            requirements_file=requirements_file,
        )

        runner_payload = {
            "run_id": payload["run_id"],
            "chunk_key": payload["chunk_key"],
            "annotation": payload.get("annotation") or {},
            "script_params": payload.get("script_params") or {},
            "items": items,
        }
        payload_path = task_root / "payload.json"
        payload_path.write_text(json.dumps(runner_payload, ensure_ascii=False), encoding="utf-8")
        command = [str(environment.python_executable), "/app/runner.py", str(script_path), str(payload_path)]
        env = self._build_subprocess_env(task_root, environment.venv_dir, bundle_environment)
        result_payload: dict[str, Any] | None = None
        script_error_detail: dict[str, Any] | None = None
        output_tail: deque[str] = deque(maxlen=SCRIPT_DIAGNOSTIC_MAX_LINES)

        def consume_script_output(stream: str, line: str) -> None:
            nonlocal result_payload, script_error_detail
            if stream == "stderr":
                if line:
                    output_tail.append(line)
                return
            if line.startswith(EVENT_PREFIX):
                event = self._parse_json_line(line[len(EVENT_PREFIX):])
                if isinstance(event, dict):
                    if event.get("level") == "error":
                        self._log_script_error(
                            payload,
                            event.get("batch_item_id"),
                            event.get("error_detail") or {"message": event.get("message")},
                        )
                    self._publish_progress(
                        str(payload["run_id"]),
                        str(payload["chunk_key"]),
                        int(event.get("processed") or 0),
                        int(event.get("total") or len(items)),
                        str(event.get("message") or "script progress"),
                        batch_item_id=event.get("batch_item_id"),
                    )
                return
            if line.startswith(LOG_PREFIX):
                log_event = self._parse_json_line(line[len(LOG_PREFIX):])
                if isinstance(log_event, dict):
                    raw_detail = log_event.get("error_detail")
                    if isinstance(raw_detail, dict):
                        script_error_detail = raw_detail
                    self._log_script_error(payload, None, raw_detail or log_event)
                return
            if line.startswith(RESULT_PREFIX):
                parsed = self._parse_json_line(line[len(RESULT_PREFIX):])
                if isinstance(parsed, dict):
                    result_payload = parsed
                    raw_detail = parsed.get("error_detail")
                    if isinstance(raw_detail, dict):
                        script_error_detail = raw_detail
                return
            if line:
                output_tail.append(line)

        remaining_timeout = self.settings.timeout_seconds - environment.elapsed_seconds
        try:
            process_result = run_isolated_process(
                command,
                cwd=task_root,
                env=env,
                stage="run_batch_script",
                timeout_seconds=remaining_timeout,
                idle_timeout_seconds=self.settings.script_runtime.idle_timeout_seconds,
                max_output_bytes=self.settings.max_output_bytes,
                resource_limit_command=self._script_resource_limit_command(),
                line_callback=consume_script_output,
            )
        except RuntimeProcessError as exc:
            raise SandboxScriptExecutionError(
                str(exc),
                error_detail=self._redact_script_diagnostic(payload, exc.error_detail),
            ) from exc

        diagnostic_output = "\n".join(output_tail)
        diagnostic_detail = self._redact_script_diagnostic(payload, script_error_detail) or {
            "source": "sandbox",
            "stage": "run_batch_script",
            "exception_type": "ProcessExit",
        }
        if isinstance(diagnostic_detail, dict):
            diagnostic_detail["exit_code"] = process_result.return_code
        if result_payload and not result_payload.get("success"):
            raise SandboxScriptExecutionError(
                str(result_payload.get("error") or "sandbox runner returned an error"),
                error_detail=diagnostic_detail,
                output_tail=self._redact_script_output(payload, diagnostic_output),
            )
        if process_result.return_code != 0:
            raise SandboxScriptExecutionError(
                f"sandbox script exited with code {process_result.return_code}",
                error_detail=diagnostic_detail,
                output_tail=self._redact_script_output(payload, diagnostic_output),
            )
        if not result_payload or not result_payload.get("success"):
            raise RuntimeError(str((result_payload or {}).get("error") or "sandbox runner returned no result"))
        return result_payload.get("data")

    def _execution_error_detail(self, payload: dict[str, Any], exc: Exception) -> dict[str, Any]:
        if isinstance(exc, SandboxScriptExecutionError):
            detail = dict(exc.error_detail)
            detail.setdefault("source", "batch_script")
            detail.setdefault("stage", "execute_batch")
            detail.setdefault("exception_type", exc.__class__.__name__)
            detail.setdefault("message", str(exc))
            if exc.output_tail:
                detail["output_tail"] = exc.output_tail
            return detail
        if isinstance(exc, ScriptEnvironmentError):
            return self._redact_script_diagnostic(payload, exc.error_detail)
        return {
            "source": "sandbox",
            "stage": "execute_chunk",
            "exception_type": exc.__class__.__name__,
            "message": str(exc),
        }

    @staticmethod
    def _redact_script_diagnostic(payload: dict[str, Any], value: Any) -> Any:
        script_params = payload.get("script_params")
        secret_values = [
            item
            for key, item in (script_params.items() if isinstance(script_params, dict) else [])
            if isinstance(item, str)
            and item
            and any(marker in str(key).lower() for marker in ("secret", "token", "api_key", "password"))
        ]

        def redact(item: Any) -> Any:
            if isinstance(item, str):
                for secret in secret_values:
                    item = item.replace(secret, "******")
                return item[:SCRIPT_DIAGNOSTIC_MAX_CHARS]
            if isinstance(item, list):
                return [redact(entry) for entry in item]
            if isinstance(item, dict):
                return {str(key): redact(entry) for key, entry in item.items()}
            return item

        return redact(value)

    def _redact_script_output(self, payload: dict[str, Any], value: str) -> str:
        return str(self._redact_script_diagnostic(payload, value))[:SCRIPT_DIAGNOSTIC_MAX_CHARS]

    def _log_script_error(self, payload: dict[str, Any], batch_item_id: Any, error_detail: Any) -> None:
        detail = self._redact_script_diagnostic(payload, error_detail)
        detail_mapping = detail if isinstance(detail, dict) else {}
        logger.error(
            "Batch script reported an error: run_id=%s chunk_key=%s batch_item_id=%s "
            "source=%s stage=%s type=%s http_status=%s request_id=%s message=%s\n"
            "traceback:\n%s\nprovider_response:\n%s",
            payload.get("run_id"),
            payload.get("chunk_key"),
            batch_item_id,
            detail_mapping.get("source"),
            detail_mapping.get("stage"),
            detail_mapping.get("exception_type"),
            detail_mapping.get("http_status"),
            detail_mapping.get("request_id"),
            detail_mapping.get("message"),
            detail_mapping.get("traceback"),
            detail_mapping.get("response_body"),
        )

    def _resolve_script_path(
        self,
        payload: dict[str, Any],
        task_root: Path,
    ) -> tuple[Path, Path | None, dict[str, str]]:
        package_path = payload.get("script_package_path")
        if isinstance(package_path, str) and package_path:
            archive_path = task_root / "script-package.zip"
            asyncio.run(self.storage.download_script_package(package_path, archive_path))
            script_root = task_root / "script"
            extract_script_package(archive_path, script_root)
            entrypoint = self._safe_entrypoint(str(payload.get("script_entrypoint") or ""))
            script_path = (script_root / entrypoint).resolve()
            try:
                script_path.relative_to(script_root.resolve())
            except ValueError as exc:
                raise RuntimeError("script entrypoint escapes extracted package") from exc
            if not script_path.is_file():
                raise RuntimeError("script entrypoint is unavailable after package extraction")
            requirements_file = script_root / "requirements.txt"
            return script_path, requirements_file if requirements_file.is_file() else None, load_package_environment(script_root)

        script_key = str(payload["script_key"])
        script_path = (self.settings.scripts_root / f"{script_key}.py").resolve()
        try:
            script_path.relative_to(self.settings.scripts_root.resolve())
        except ValueError as exc:
            raise RuntimeError("script path escapes sandbox scripts directory") from exc
        if not script_path.is_file():
            raise RuntimeError(f"registered script `{script_key}` is not installed")
        return script_path, None, {}

    @staticmethod
    def _safe_entrypoint(value: str) -> Path:
        normalized = value.strip().replace("\\", "/")
        path = Path(normalized)
        if not normalized.endswith(".py") or path.is_absolute() or ".." in path.parts:
            raise RuntimeError("script entrypoint must be a relative Python file")
        return path

    def _normalize_results(self, items: list[dict[str, Any]], result: Any) -> list[dict[str, Any]]:
        returned_items = result.get("items") if isinstance(result, dict) and isinstance(result.get("items"), list) else []
        by_item_id = {
            item.get("batch_item_id"): item
            for item in returned_items
            if isinstance(item, dict) and isinstance(item.get("batch_item_id"), int)
        }
        normalized: list[dict[str, Any]] = []
        for item in items:
            batch_item_id = item["batch_item_id"]
            script_item = by_item_id.get(batch_item_id)
            if script_item is None:
                normalized.append({
                    "batch_item_id": batch_item_id,
                    "status": "failed",
                    "error": "script omitted this sample",
                    "error_detail": {
                        "source": "batch_script",
                        "stage": "result_contract",
                        "message": "script omitted this sample",
                    },
                })
                continue
            normalized.append(script_item)
        return normalized

    def _failed_results(
        self,
        payload: dict[str, Any],
        error: str,
        stage: str,
        *,
        error_detail: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        items = payload.get("items") if isinstance(payload.get("items"), list) else []
        return [
            {
                "batch_item_id": item.get("batch_item_id"),
                "status": "failed",
                "error": error,
                "error_detail": error_detail or {
                    "source": "sandbox",
                    "stage": stage,
                    "message": error,
                },
            }
            for item in items
            if isinstance(item, dict)
        ]

    def _publish_progress(
        self,
        run_id: str,
        chunk_key: str,
        processed: int,
        total: int,
        message: str,
        *,
        phase: str = "execution",
        batch_item_id: int | None = None,
    ) -> None:
        payload = {
            "message_type": "pipeline.batch.progress",
            "service_name": "ai_pipeline_sandbox",
            "run_id": run_id,
            "chunk_key": chunk_key,
            "processed": processed,
            "total": total,
            "message": message,
            "phase": phase,
        }
        if isinstance(batch_item_id, int) and not isinstance(batch_item_id, bool):
            payload["batch_item_id"] = batch_item_id
        self._publish(
            self.settings.rabbitmq.progress_routing_key,
            payload,
        )

    def _publish_result(self, run_id: str, chunk_key: str, results: list[dict[str, Any]]) -> None:
        self._publish(
            self.settings.rabbitmq.result_routing_key,
            {
                "message_type": "pipeline.batch.result",
                "service_name": "ai_pipeline_sandbox",
                "run_id": run_id,
                "chunk_key": chunk_key,
                "results": results,
            },
        )

    def _publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        if not self._channel:
            raise RuntimeError("RabbitMQ channel is unavailable")
        self._channel.basic_publish(
            exchange=self.settings.rabbitmq.exchange_name,
            routing_key=routing_key,
            body=json.dumps(payload, ensure_ascii=False),
            properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
        )

    def _build_subprocess_env(
        self,
        task_root: Path,
        venv_dir: Path,
        bundle_environment: dict[str, str],
    ) -> dict[str, str]:
        task_home = task_root / "home"
        task_tmp = task_root / "tmp"
        task_home.mkdir(parents=True, exist_ok=True)
        task_tmp.mkdir(parents=True, exist_ok=True)
        environment = {**os.environ, **bundle_environment}
        environment.update({
            "PATH": f"{venv_dir / 'bin'}:{os.getenv('PATH', '/usr/local/bin:/usr/bin:/bin')}",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUNBUFFERED": "1",
            "LANG": os.getenv("LANG", "C.UTF-8"),
            "LC_ALL": os.getenv("LC_ALL", "C.UTF-8"),
            "HOME": str(task_home),
            "XDG_CACHE_HOME": str(task_home / ".cache"),
            "XDG_CONFIG_HOME": str(task_home / ".config"),
            "TMPDIR": str(task_tmp),
            "TMP": str(task_tmp),
            "TEMP": str(task_tmp),
            "VIRTUAL_ENV": str(venv_dir),
            "PIP_CACHE_DIR": str(self.settings.script_runtime.pip_cache_dir),
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INPUT": "1",
        })
        return environment

    def _script_resource_limit_command(self) -> list[str]:
        return self._resource_limit_command(self.settings.max_processes)

    def _environment_resource_limit_command(self) -> list[str]:
        return self._resource_limit_command(
            max(
                self.settings.max_processes,
                self.settings.script_runtime.bootstrap_max_processes,
            )
        )

    def _resource_limit_command(self, max_processes: int) -> list[str]:
        if os.name == "nt":
            return []
        prlimit = shutil.which("prlimit")
        if not prlimit:
            logger.warning("prlimit is unavailable; sandbox subprocess resource limits are disabled")
            return []
        limits = (
            ("--cpu", self.settings.cpu_seconds),
            ("--as", self.settings.memory_bytes),
            ("--fsize", self.settings.script_runtime.process_fsize_bytes),
            ("--nproc", max_processes),
            ("--nofile", self.settings.script_runtime.process_nofile),
            ("--core", 0),
        )
        return [
            prlimit,
            *(f"{option}={value}" for option, value in limits if value > 0 or option == "--core"),
            "--",
        ]

    @staticmethod
    def _parse_json_line(raw: str) -> Any:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def _close(self) -> None:
        channel = self._channel
        connection = self._connection
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
