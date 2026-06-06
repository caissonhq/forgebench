from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any


_CONFIGURED = False
_LOGGER = logging.getLogger("forgebench")


def configure_logging(*, level: str | None = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    resolved = (level or os.environ.get("FORGEBENCH_LOG_LEVEL", "INFO")).upper()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter())
    _LOGGER.handlers.clear()
    _LOGGER.addHandler(handler)
    _LOGGER.setLevel(getattr(logging, resolved, logging.INFO))
    _LOGGER.propagate = False
    _CONFIGURED = True


def log_event(level: str, event: str, **fields: Any) -> None:
    configure_logging()
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
        **fields,
    }
    message = json.dumps(payload, sort_keys=True, default=str)
    numeric = getattr(logging, level.upper(), logging.INFO)
    _LOGGER.log(numeric, message)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return record.getMessage()