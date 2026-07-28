"""批量标注任务 SSE 推送。"""
import asyncio
import json
from collections import defaultdict
from contextlib import suppress
from dataclasses import dataclass
from typing import Any


@dataclass
class BatchRunStreamEvent:
    event: str
    run_id: str
    data: dict[str, Any]

    def to_sse_payload(self) -> dict[str, str]:
        return {
            "event": self.event,
            "data": json.dumps(self.data, ensure_ascii=False, default=str),
        }


class BatchRunStreamHub:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._subscribers: dict[int, asyncio.Queue[BatchRunStreamEvent]] = {}
        self._run_subscribers: dict[str, set[int]] = defaultdict(set)
        self._next_id = 1

    async def subscribe(self, run_id: str) -> tuple[int, asyncio.Queue[BatchRunStreamEvent]]:
        queue: asyncio.Queue[BatchRunStreamEvent] = asyncio.Queue(maxsize=200)
        async with self._lock:
            subscriber_id = self._next_id
            self._next_id += 1
            self._subscribers[subscriber_id] = queue
            self._run_subscribers[run_id].add(subscriber_id)
        return subscriber_id, queue

    async def unsubscribe(self, subscriber_id: int, run_id: str) -> None:
        async with self._lock:
            self._subscribers.pop(subscriber_id, None)
            run_subscribers = self._run_subscribers.get(run_id)
            if run_subscribers is not None:
                run_subscribers.discard(subscriber_id)
                if not run_subscribers:
                    self._run_subscribers.pop(run_id, None)

    async def publish(self, event: BatchRunStreamEvent) -> None:
        async with self._lock:
            targets = [
                self._subscribers[subscriber_id]
                for subscriber_id in self._run_subscribers.get(event.run_id, set())
                if subscriber_id in self._subscribers
            ]

        for queue in targets:
            with suppress(asyncio.QueueFull):
                queue.put_nowait(event)


_batch_run_stream_hub: BatchRunStreamHub | None = None


def get_batch_run_stream_hub() -> BatchRunStreamHub:
    global _batch_run_stream_hub
    if _batch_run_stream_hub is None:
        _batch_run_stream_hub = BatchRunStreamHub()
    return _batch_run_stream_hub
