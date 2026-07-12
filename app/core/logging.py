"""JSON logging for the API and the worker.

One line of JSON per log record on stdout:

    {"timestamp": "...", "level": "INFO", "logger": "app.execution.engine",
     "message": "agent dispatched", "event": "agent_dispatched",
     "workflow_execution_id": "...", ...}

Anything passed via ``logger.info(msg, extra={...})`` is merged into the JSON
object, so engine/worker events carry their ids as queryable fields instead of
being formatted into the message. SQLAlchemy loggers are capped at WARNING —
SQL statement echo is opt-in via the SQL_ECHO setting, not tied to DEBUG.
"""
import json
import logging
import sys
from datetime import datetime, timezone

# Attributes present on every LogRecord — anything else came in via ``extra``.
# ``color_message`` is uvicorn's ANSI-colored duplicate of ``message``; drop it.
_STANDARD_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message", "asctime",
    "color_message",
})

_NOISY_LOGGERS = (
    "sqlalchemy.engine",
    "sqlalchemy.pool",
    "sqlalchemy.dialects",
    "sqlalchemy.orm",
    "aiosqlite",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # default=str renders UUIDs/datetimes; never let logging itself crash.
        return json.dumps(payload, default=str)


def setup_logging() -> None:
    """Install the JSON handler on the root logger (idempotent via force=True).

    Call once at process start — the API does it in app.main, the worker in
    app.worker. Uvicorn's own loggers are re-routed through the root handler so
    its startup/access lines come out as JSON too.
    """
    from app.core.config import get_settings  # late import: avoid cycles

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(
        level=get_settings().log_level.upper(), handlers=[handler], force=True
    )

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True
