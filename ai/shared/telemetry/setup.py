"""Install the process's single log handler, as plain text or JSON."""

from __future__ import annotations

import logging
import sys
from typing import Literal, TextIO, TypedDict

from shared.telemetry.json_formatter import JsonFormatter

LogFormat = Literal["text", "json"]
# uvicorn installs its own handlers, which would write plain-text lines.
_UVICORN_LOGGERS = ("uvicorn", "uvicorn.error")


class _TelemetryHandler(logging.StreamHandler[TextIO]):
    """The stdout handler this module installs, so a second call can replace it."""


class FormatterArgs(TypedDict):
    """The fixed fields the JSON formatter writes on every line."""

    service: str
    api_version: str
    revision: str | None
    gcp_project_id: str | None


def configure_logging(
    level: str, log_format: LogFormat, formatter_args: FormatterArgs
) -> None:
    """Install one stdout handler on the root logger; safe to call twice.

    Only a handler installed by an earlier call is replaced, so handlers added
    by others (pytest's log capture) keep working.
    """
    handler = _TelemetryHandler(sys.stdout)
    if log_format == "json":
        handler.setFormatter(JsonFormatter(**formatter_args))
        _route_uvicorn_to_root()
    else:
        handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    root = logging.getLogger()
    for old in root.handlers[:]:
        if isinstance(old, _TelemetryHandler):
            root.removeHandler(old)
    root.addHandler(handler)
    root.setLevel(level.upper())


def _route_uvicorn_to_root() -> None:
    for name in _UVICORN_LOGGERS:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    # The access log has the raw path and query string; http.request replaces it.
    logging.getLogger("uvicorn.access").disabled = True
