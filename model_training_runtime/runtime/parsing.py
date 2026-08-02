"""Strict parsing for the dormant runner's line-oriented protocol."""
from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from contracts import TrainingResult, training_event_adapter

from .models import RunnerMessage
from .protocol import EVENT_PREFIX, LOG_PREFIX, RESULT_PREFIX


class RunnerProtocolError(ValueError):
    """A runner output line cannot be accepted by the future worker."""


def parse_runner_line(line: str) -> RunnerMessage | None:
    """Parse a prefixed runner line; ordinary package stdout returns ``None``."""
    channel: str | None = None
    content = ""
    if line.startswith(EVENT_PREFIX):
        channel, content = "event", line[len(EVENT_PREFIX):]
    elif line.startswith(LOG_PREFIX):
        channel, content = "log", line[len(LOG_PREFIX):]
    elif line.startswith(RESULT_PREFIX):
        channel, content = "result", line[len(RESULT_PREFIX):]
    else:
        return None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RunnerProtocolError(f"runner emitted invalid {channel} JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RunnerProtocolError(f"runner emitted {channel} payload that is not an object")
    try:
        if channel == "event":
            validated = training_event_adapter.validate_python(payload)
            return RunnerMessage(channel="event", payload=validated.model_dump(mode="json"))
        if channel == "result":
            validated_result = TrainingResult.model_validate(payload)
            return RunnerMessage(channel="result", payload=validated_result.model_dump(mode="json"))
    except ValidationError as exc:
        raise RunnerProtocolError(f"runner emitted invalid {channel} payload: {exc}") from exc
    _validate_log(payload)
    return RunnerMessage(channel="log", payload=payload)


def _validate_log(payload: dict[str, Any]) -> None:
    level = payload.get("level")
    message = payload.get("message")
    if level not in {"debug", "info", "warning", "error"}:
        raise RunnerProtocolError("runner log level must be debug, info, warning, or error")
    if not isinstance(message, str) or not message:
        raise RunnerProtocolError("runner log message must be a non-empty string")
