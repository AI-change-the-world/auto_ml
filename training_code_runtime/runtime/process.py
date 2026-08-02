"""Bounded subprocess execution shared by future training worker stages."""
from __future__ import annotations

import codecs
import os
import queue
import signal
import subprocess
import threading
import time
from collections import deque
from pathlib import Path
from typing import Callable

from .errors import RuntimeExecutionError
from .logging_utils import logger
from .models import ProcessResult


OUTPUT_TAIL_LIMIT = 16 * 1024
LineCallback = Callable[[str, str], None]


class RuntimeProcessError(RuntimeExecutionError):
    pass


def run_isolated_process(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stage: str,
    timeout_seconds: float,
    idle_timeout_seconds: int,
    max_output_bytes: int,
    resource_limit_command: list[str] | None = None,
    line_callback: LineCallback | None = None,
) -> ProcessResult:
    """Run one stage with bounded output and whole-process-tree termination."""
    if timeout_seconds <= 0:
        raise _process_error(stage, "TimeoutError", f"{stage} exceeded the total training timeout")
    try:
        logger.info("Starting training subprocess: stage=%s cwd=%s command=%s", stage, cwd, " ".join(command))
        process = subprocess.Popen(
            [*(resource_limit_command or []), *command],
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            bufsize=0,
            start_new_session=os.name != "nt",
        )
    except OSError as exc:
        raise _process_error(stage, exc.__class__.__name__, f"{stage} could not start: {exc}") from exc

    output_queue: queue.Queue[tuple[str, bytes | None]] = queue.Queue()
    readers = [
        _start_reader(process.stdout, "stdout", output_queue),
        _start_reader(process.stderr, "stderr", output_queue),
    ]
    started_at = time.monotonic()
    last_output_at = started_at
    closed_streams = 0
    stdout_bytes = 0
    stderr_bytes = 0
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    stdout_tail: deque[str] = deque()
    stderr_tail: deque[str] = deque()
    tail_size = {"stdout": 0, "stderr": 0}
    decoders = {
        "stdout": codecs.getincrementaldecoder("utf-8")(errors="replace"),
        "stderr": codecs.getincrementaldecoder("utf-8")(errors="replace"),
    }
    line_buffers = {"stdout": "", "stderr": ""}

    try:
        while process.poll() is None or closed_streams < 2:
            try:
                stream, chunk = output_queue.get(timeout=0.2)
            except queue.Empty:
                stream, chunk = "", None
            if stream:
                if chunk is None:
                    closed_streams += 1
                else:
                    last_output_at = time.monotonic()
                    if stream == "stdout":
                        stdout_bytes += len(chunk)
                    else:
                        stderr_bytes += len(chunk)
                    if max_output_bytes > 0 and (
                        stdout_bytes > max_output_bytes or stderr_bytes > max_output_bytes
                    ):
                        _terminate_process_tree(process)
                        raise _process_error(
                            stage,
                            "OutputLimitExceeded",
                            f"{stage} exceeded the {max_output_bytes} byte output limit",
                            stdout_bytes=stdout_bytes,
                            stderr_bytes=stderr_bytes,
                            output_tail=_combined_tail(stdout_tail, stderr_tail),
                        )
                    text = decoders[stream].decode(chunk)
                    if text:
                        if stream == "stdout":
                            stdout_chunks.append(text)
                        else:
                            stderr_chunks.append(text)
                        _append_tail(stdout_tail if stream == "stdout" else stderr_tail, tail_size, stream, text)
                        line_buffers[stream] += text
                        _emit_complete_lines(stream, line_buffers, line_callback)

            now = time.monotonic()
            if now - started_at >= timeout_seconds:
                _terminate_process_tree(process)
                raise _process_error(
                    stage,
                    "TimeoutError",
                    f"{stage} timed out after {int(timeout_seconds)} seconds",
                    stdout_bytes=stdout_bytes,
                    stderr_bytes=stderr_bytes,
                    output_tail=_combined_tail(stdout_tail, stderr_tail),
                )
            if idle_timeout_seconds > 0 and now - last_output_at >= idle_timeout_seconds:
                _terminate_process_tree(process)
                raise _process_error(
                    stage,
                    "IdleTimeoutError",
                    f"{stage} idle timeout after {idle_timeout_seconds} seconds",
                    stdout_bytes=stdout_bytes,
                    stderr_bytes=stderr_bytes,
                    output_tail=_combined_tail(stdout_tail, stderr_tail),
                )
    except Exception:
        _terminate_process_tree(process)
        raise
    finally:
        _wait_for_process(process)
        for reader in readers:
            reader.join(timeout=1)
        for stream in ("stdout", "stderr"):
            final_text = decoders[stream].decode(b"", final=True)
            if final_text:
                if stream == "stdout":
                    stdout_chunks.append(final_text)
                else:
                    stderr_chunks.append(final_text)
                _append_tail(stdout_tail if stream == "stdout" else stderr_tail, tail_size, stream, final_text)
                line_buffers[stream] += final_text
            if line_buffers[stream] and line_callback:
                line_callback(stream, line_buffers[stream])

    result = ProcessResult(
        return_code=process.returncode or 0,
        stdout="".join(stdout_chunks),
        stderr="".join(stderr_chunks),
        stdout_bytes=stdout_bytes,
        stderr_bytes=stderr_bytes,
    )
    logger.info(
        "Training subprocess completed: stage=%s exit_code=%s elapsed_seconds=%.2f stdout_bytes=%s stderr_bytes=%s",
        stage,
        result.return_code,
        time.monotonic() - started_at,
        result.stdout_bytes,
        result.stderr_bytes,
    )
    return result


def _start_reader(stream, stream_name: str, output_queue: queue.Queue[tuple[str, bytes | None]]) -> threading.Thread:
    def read_output() -> None:
        if stream is None:
            output_queue.put((stream_name, None))
            return
        try:
            while True:
                chunk = stream.read(4096)
                if not chunk:
                    break
                output_queue.put((stream_name, chunk))
        finally:
            stream.close()
            output_queue.put((stream_name, None))

    reader = threading.Thread(target=read_output, name=f"training-{stream_name}-reader", daemon=True)
    reader.start()
    return reader


def _emit_complete_lines(stream: str, line_buffers: dict[str, str], callback: LineCallback | None) -> None:
    buffer = line_buffers[stream]
    while True:
        positions = [position for position in (buffer.find("\n"), buffer.find("\r")) if position >= 0]
        if not positions:
            break
        split_at = min(positions)
        line = buffer[:split_at]
        delimiter = buffer[split_at]
        buffer = buffer[split_at + 1 :]
        if delimiter == "\r" and buffer.startswith("\n"):
            buffer = buffer[1:]
        if callback:
            callback(stream, line)
    line_buffers[stream] = buffer


def _append_tail(tail: deque[str], tail_size: dict[str, int], stream: str, text: str) -> None:
    tail.append(text)
    tail_size[stream] += len(text.encode("utf-8", errors="replace"))
    while tail and tail_size[stream] > OUTPUT_TAIL_LIMIT:
        removed = tail.popleft()
        tail_size[stream] -= len(removed.encode("utf-8", errors="replace"))


def _combined_tail(stdout_tail: deque[str], stderr_tail: deque[str]) -> str:
    stdout = "".join(stdout_tail)
    stderr = "".join(stderr_tail)
    if stdout and stderr:
        return f"stdout:\n{stdout}\nstderr:\n{stderr}"
    return stdout or stderr


def _process_error(stage: str, exception_type: str, message: str, **extra: object) -> RuntimeProcessError:
    return RuntimeProcessError(
        message,
        {
            "source": "training_code_runtime",
            "stage": stage,
            "exception_type": exception_type,
            "message": message,
            **extra,
        },
    )


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        process.kill()
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        process.kill()


def _wait_for_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _terminate_process_tree(process)
        process.wait()
