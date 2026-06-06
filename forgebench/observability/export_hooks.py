from __future__ import annotations

import os
from typing import Any


OTEL_ENDPOINT_ENV = "FORGEBENCH_OTEL_ENDPOINT"
SENTRY_DSN_ENV = "FORGEBENCH_SENTRY_DSN"


def maybe_export_span(name: str, attributes: dict[str, Any] | None = None) -> None:
    endpoint = os.environ.get(OTEL_ENDPOINT_ENV, "").strip()
    if not endpoint:
        return
    # Optional hook: operators wire OTEL collector in enterprise deployments.
    del name, attributes


def maybe_export_exception(exc: BaseException, *, context: str) -> None:
    dsn = os.environ.get(SENTRY_DSN_ENV, "").strip()
    if not dsn:
        return
    del exc, context