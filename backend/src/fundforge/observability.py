"""Operational telemetry: Prometheus metrics and one-line JSON logs. Never part of game state.

Label values are bounded: command types outside the registry are reported as ``unknown`` and
error codes come from the API's fixed set, so clients cannot grow the metric series.
"""

import contextvars
import json
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from prometheus_client import Counter, Histogram

from .governance import COMMANDS

COMMAND_SECONDS = Histogram("fundforge_command_seconds", "Time to apply one command, including bot replies",
                            ["type"])
REPLAY_SECONDS = Histogram("fundforge_replay_seconds", "Time to rebuild a room session from its command log")
REJECTIONS = Counter("fundforge_rejections_total", "HTTP errors returned, by envelope code", ["code"])

request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
KNOWN = frozenset(COMMANDS) | {"tick"}


def command_type(command: dict[str, Any]) -> str:
    t = command.get("type")
    return t if isinstance(t, str) and t in KNOWN else "unknown"


@contextmanager
def timed(histogram: Histogram, **labels: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        (histogram.labels(**labels) if labels else histogram).observe(time.perf_counter() - start)


def context(**fields: Any) -> dict[str, Any]:
    """``extra`` for a log call: the fields plus the current request id, captured when logged."""
    return {**fields, "request_id": request_id.get()}


class JsonFormatter(logging.Formatter):
    """One JSON object per line: time, level, logger, message, request id and any ``extra`` fields."""

    FIELDS = ("room", "seq", "command", "status", "method", "path", "ms", "code")

    def format(self, record: logging.LogRecord) -> str:
        out: dict[str, Any] = {"ts": round(record.created, 3), "level": record.levelname, "logger": record.name,
                               "msg": record.getMessage(),
                               "request_id": getattr(record, "request_id", None) or request_id.get()}
        out.update({k: getattr(record, k) for k in self.FIELDS if hasattr(record, k)})
        if record.exc_info:
            out["exc"] = self.formatException(record.exc_info)
        return json.dumps(out, separators=(",", ":"), default=str)
