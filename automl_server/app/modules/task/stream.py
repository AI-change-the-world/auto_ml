"""任务 SSE 推送"""
import asyncio
import json
from collections import defaultdict
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from loguru import logger


@dataclass
class StreamEvent:
    event: str
    data: dict[str, Any]
    task_id: Optional[int] = None

    def to_sse_payload(self) -> dict[str, str]:
        return {
            "event": self.event,
            "data": json.dumps(self.data, ensure_ascii=False, default=_json_default),
        }


def _json_default(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class TaskStreamHub:
    """进程内任务事件广播中心"""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._subscribers: dict[int, asyncio.Queue[StreamEvent]] = {}
        self._global_subscribers: set[int] = set()
        self._task_subscribers: dict[int, set[int]] = defaultdict(set)
        self._next_id = 1

    async def subscribe(self, task_id: Optional[int] = None) -> tuple[int, asyncio.Queue[StreamEvent]]:
        queue: asyncio.Queue[StreamEvent] = asyncio.Queue(maxsize=200)
        async with self._lock:
            subscriber_id = self._next_id
            self._next_id += 1
            self._subscribers[subscriber_id] = queue
            if task_id is None:
                self._global_subscribers.add(subscriber_id)
            else:
                self._task_subscribers[task_id].add(subscriber_id)
        logger.debug(f"Task stream subscriber connected: id={subscriber_id}, task_id={task_id}")
        return subscriber_id, queue

    async def unsubscribe(self, subscriber_id: int, task_id: Optional[int] = None):
        async with self._lock:
            self._subscribers.pop(subscriber_id, None)
            if task_id is None:
                self._global_subscribers.discard(subscriber_id)
            else:
                task_subscribers = self._task_subscribers.get(task_id)
                if task_subscribers is not None:
                    task_subscribers.discard(subscriber_id)
                    if not task_subscribers:
                        self._task_subscribers.pop(task_id, None)
        logger.debug(f"Task stream subscriber disconnected: id={subscriber_id}, task_id={task_id}")

    async def publish(self, event: StreamEvent):
        async with self._lock:
            if event.task_id is None:
                targets = [
                    self._subscribers[sid]
                    for sid in self._global_subscribers
                    if sid in self._subscribers
                ]
            else:
                general_targets = [
                    self._subscribers[sid]
                    for sid in self._global_subscribers
                    if sid in self._subscribers
                ]
                task_targets = [
                    self._subscribers[sid]
                    for sid in self._task_subscribers.get(event.task_id, set())
                    if sid in self._subscribers
                ]
                targets = general_targets + task_targets

        for queue in targets:
            with suppress(asyncio.QueueFull):
                queue.put_nowait(event)


_task_stream_hub: Optional[TaskStreamHub] = None


def get_task_stream_hub() -> TaskStreamHub:
    global _task_stream_hub
    if _task_stream_hub is None:
        _task_stream_hub = TaskStreamHub()
    return _task_stream_hub
