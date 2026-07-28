"""RabbitMQ consumer that executes platform batch scripts in isolated subprocesses."""
from __future__ import annotations

import asyncio
import json
import os
import queue
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any

import pika

from config import SandboxSettings
from storage import DatasetStorage

try:
    import resource
except ImportError:  # pragma: no cover - Windows does not expose resource
    resource = None


EVENT_PREFIX = "__AUTO_ML_BATCH_EVENT__="
RESULT_PREFIX = "__AUTO_ML_BATCH_RESULT__="
SCRIPT_ARCHIVE_MAX_FILES = 512
SCRIPT_ARCHIVE_MAX_UNPACKED_BYTES = 512 * 1024 * 1024


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

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.settings.workspace_root.mkdir(parents=True, exist_ok=True)
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._consume_loop, name="pipeline-sandbox-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._thread = None

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
                    time.sleep(2)
            finally:
                self._close()

    def _on_message(self, channel, method, _properties, body: bytes) -> None:
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
            if run_id and chunk_key:
                self._publish_result(run_id, chunk_key, self._failed_results(payload, f"sandbox error: {exc}"))
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
            self._publish_progress(run_id, chunk_key, 0, len(payload.get("items") or []), "sandbox started")
            runnable_items, failed_results = self._prepare_inputs(payload, task_root)
            if runnable_items:
                script_result = self._run_script(payload, runnable_items, task_root)
                results = self._normalize_results(runnable_items, script_result)
            else:
                results = []
            results.extend(failed_results)
            self._publish_result(run_id, chunk_key, results)
        except Exception as exc:
            self._publish_result(run_id, chunk_key, self._failed_results(payload, f"sandbox error: {exc}"))
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
        for index, raw_item in enumerate(items, start=1):
            if not isinstance(raw_item, dict):
                continue
            batch_item_id = raw_item.get("batch_item_id")
            asset_path = raw_item.get("asset_path")
            if not isinstance(batch_item_id, int) or not isinstance(asset_path, str) or not asset_path:
                failed_results.append({"batch_item_id": batch_item_id, "status": "failed", "error": "sample asset path is unavailable"})
                continue
            file_name = str(raw_item.get("asset_file_name") or f"sample_{batch_item_id}")
            destination = task_root / "inputs" / f"{batch_item_id}_{Path(file_name).name}"
            try:
                asyncio.run(self.storage.download(asset_path, destination))
            except Exception as exc:
                failed_results.append({"batch_item_id": batch_item_id, "status": "failed", "error": f"failed to download sample: {exc}"})
                continue
            item = dict(raw_item)
            item["local_path"] = str(destination)
            runnable_items.append(item)
            self._publish_progress(
                str(payload["run_id"]),
                str(payload["chunk_key"]),
                index,
                len(items),
                "sample input prepared",
            )
        return runnable_items, failed_results

    def _run_script(self, payload: dict[str, Any], items: list[dict[str, Any]], task_root: Path) -> Any:
        script_path = self._resolve_script_path(payload, task_root)

        runner_payload = {
            "run_id": payload["run_id"],
            "chunk_key": payload["chunk_key"],
            "annotation": payload.get("annotation") or {},
            "script_params": payload.get("script_params") or {},
            "items": items,
        }
        payload_path = task_root / "payload.json"
        payload_path.write_text(json.dumps(runner_payload, ensure_ascii=False), encoding="utf-8")
        command = [sys.executable, "/app/runner.py", str(script_path), str(payload_path)]
        env = self._build_subprocess_env(task_root)
        process = subprocess.Popen(
            command,
            cwd=str(task_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
            start_new_session=True,
            preexec_fn=self._limit_resources if resource is not None else None,
        )
        timed_out = threading.Event()

        def kill_on_timeout() -> None:
            timed_out.set()
            self._terminate_process_group(process)

        timer = threading.Timer(self.settings.timeout_seconds, kill_on_timeout)
        timer.start()
        output_size = 0
        result_payload: dict[str, Any] | None = None
        try:
            assert process.stdout is not None
            for raw_line in process.stdout:
                output_size += len(raw_line.encode("utf-8", errors="replace"))
                if output_size > self.settings.max_output_bytes:
                    self._terminate_process_group(process)
                    raise RuntimeError("sandbox script exceeded stdout limit")
                line = raw_line.rstrip("\n")
                if line.startswith(EVENT_PREFIX):
                    event = self._parse_json_line(line[len(EVENT_PREFIX):])
                    if isinstance(event, dict):
                        self._publish_progress(
                            str(payload["run_id"]),
                            str(payload["chunk_key"]),
                            int(event.get("processed") or 0),
                            int(event.get("total") or len(items)),
                            str(event.get("message") or "script progress"),
                        )
                    continue
                if line.startswith(RESULT_PREFIX):
                    parsed = self._parse_json_line(line[len(RESULT_PREFIX):])
                    if isinstance(parsed, dict):
                        result_payload = parsed
            return_code = process.wait(timeout=10)
        finally:
            timer.cancel()
        if timed_out.is_set():
            raise RuntimeError("sandbox script timed out")
        if return_code != 0:
            raise RuntimeError("sandbox script exited with an error")
        if not result_payload or not result_payload.get("success"):
            raise RuntimeError(str((result_payload or {}).get("error") or "sandbox runner returned no result"))
        return result_payload.get("data")

    def _resolve_script_path(self, payload: dict[str, Any], task_root: Path) -> Path:
        package_path = payload.get("script_package_path")
        if isinstance(package_path, str) and package_path:
            archive_path = task_root / "script-package.zip"
            asyncio.run(self.storage.download_script_package(package_path, archive_path))
            script_root = task_root / "script"
            self._extract_script_package(archive_path, script_root)
            entrypoint = self._safe_entrypoint(str(payload.get("script_entrypoint") or ""))
            script_path = (script_root / entrypoint).resolve()
            try:
                script_path.relative_to(script_root.resolve())
            except ValueError as exc:
                raise RuntimeError("script entrypoint escapes extracted package") from exc
            if not script_path.is_file():
                raise RuntimeError("script entrypoint is unavailable after package extraction")
            return script_path

        script_key = str(payload["script_key"])
        script_path = (self.settings.scripts_root / f"{script_key}.py").resolve()
        try:
            script_path.relative_to(self.settings.scripts_root.resolve())
        except ValueError as exc:
            raise RuntimeError("script path escapes sandbox scripts directory") from exc
        if not script_path.is_file():
            raise RuntimeError(f"registered script `{script_key}` is not installed")
        return script_path

    @staticmethod
    def _safe_entrypoint(value: str) -> Path:
        normalized = value.strip().replace("\\", "/")
        path = Path(normalized)
        if not normalized.endswith(".py") or path.is_absolute() or ".." in path.parts:
            raise RuntimeError("script entrypoint must be a relative Python file")
        return path

    @staticmethod
    def _extract_script_package(archive_path: Path, destination: Path) -> None:
        try:
            archive = zipfile.ZipFile(archive_path)
        except zipfile.BadZipFile as exc:
            raise RuntimeError("downloaded script package is not a ZIP archive") from exc
        with archive:
            infos = archive.infolist()
            if len(infos) > SCRIPT_ARCHIVE_MAX_FILES:
                raise RuntimeError("script package contains too many files")
            total_size = 0
            destination.mkdir(parents=True, exist_ok=True)
            destination_root = destination.resolve()
            for info in infos:
                member_path = Path(info.filename)
                mode = info.external_attr >> 16
                if member_path.is_absolute() or ".." in member_path.parts or stat.S_ISLNK(mode):
                    raise RuntimeError("script package contains an unsafe file path")
                target = (destination / member_path).resolve()
                try:
                    target.relative_to(destination_root)
                except ValueError as exc:
                    raise RuntimeError("script package path escapes task directory") from exc
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                total_size += info.file_size
                if total_size > SCRIPT_ARCHIVE_MAX_UNPACKED_BYTES:
                    raise RuntimeError("script package exceeds extraction limit")
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)

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
                normalized.append({"batch_item_id": batch_item_id, "status": "failed", "error": "script omitted this sample"})
                continue
            normalized.append(script_item)
        return normalized

    def _failed_results(self, payload: dict[str, Any], error: str) -> list[dict[str, Any]]:
        items = payload.get("items") if isinstance(payload.get("items"), list) else []
        return [
            {"batch_item_id": item.get("batch_item_id"), "status": "failed", "error": error}
            for item in items
            if isinstance(item, dict)
        ]

    def _publish_progress(self, run_id: str, chunk_key: str, processed: int, total: int, message: str) -> None:
        self._publish(
            self.settings.rabbitmq.progress_routing_key,
            {
                "message_type": "pipeline.batch.progress",
                "service_name": "ai_pipeline_sandbox",
                "run_id": run_id,
                "chunk_key": chunk_key,
                "processed": processed,
                "total": total,
                "message": message,
            },
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

    def _build_subprocess_env(self, task_root: Path) -> dict[str, str]:
        task_home = task_root / "home"
        task_tmp = task_root / "tmp"
        task_home.mkdir(parents=True, exist_ok=True)
        task_tmp.mkdir(parents=True, exist_ok=True)
        return {
            "PATH": os.getenv("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUNBUFFERED": "1",
            "LANG": os.getenv("LANG", "C.UTF-8"),
            "LC_ALL": os.getenv("LC_ALL", "C.UTF-8"),
            "HOME": str(task_home),
            "TMPDIR": str(task_tmp),
            "TMP": str(task_tmp),
            "TEMP": str(task_tmp),
        }

    def _limit_resources(self) -> None:
        if resource is None:
            return
        resource.setrlimit(resource.RLIMIT_CPU, (self.settings.cpu_seconds, self.settings.cpu_seconds))
        resource.setrlimit(resource.RLIMIT_AS, (self.settings.memory_bytes, self.settings.memory_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (self.settings.max_output_bytes, self.settings.max_output_bytes))
        resource.setrlimit(resource.RLIMIT_NPROC, (self.settings.max_processes, self.settings.max_processes))
        resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))

    @staticmethod
    def _parse_json_line(raw: str) -> Any:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _terminate_process_group(process: subprocess.Popen) -> None:
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            time.sleep(0.2)
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

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
