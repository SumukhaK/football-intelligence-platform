"""Format log records as one JSON object per line (telemetry contract section 1)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from shared.telemetry.context import get_request_id

CONTRACT_VERSION = "1.0.0"
COMMON_FIELDS = (
    "timestamp",
    "severity",
    "message",
    "logger",
    "event",
    "request_id",
    "logging.googleapis.com/trace",
    "logging.googleapis.com/spanId",
    "trace_id",
    "service",
    "revision",
    "api_version",
    "contract_version",
    "attributes",
)


def _timestamp(created: float) -> str:
    moment = datetime.fromtimestamp(created, UTC)
    return moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class JsonFormatter(logging.Formatter):
    """Writes the contract's common fields, plus exception fields on errors."""

    def __init__(
        self,
        *,
        service: str,
        api_version: str,
        revision: str | None,
        gcp_project_id: str | None,
    ) -> None:
        """Fix the fields that are the same on every line of this process."""
        super().__init__()
        self._service = service
        self._api_version = api_version
        self._revision = revision
        # Cloud Logging's trace key needs the project ID once spans exist (M4).
        self._gcp_project_id = gcp_project_id

    def format(self, record: logging.LogRecord) -> str:
        """Return ``record`` as one line of JSON."""
        line: dict[str, Any] = {
            "timestamp": _timestamp(record.created),
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "event": getattr(record, "event", None),
            "request_id": get_request_id(),
            "logging.googleapis.com/trace": None,
            "logging.googleapis.com/spanId": None,
            "trace_id": None,
            "service": self._service,
            "revision": self._revision,
            "api_version": self._api_version,
            "contract_version": CONTRACT_VERSION,
            "attributes": getattr(record, "attributes", {}),
        }
        attributes = line["attributes"]
        if isinstance(attributes, dict) and "exception_type" in attributes:
            line["exception_type"] = attributes["exception_type"]
        if record.exc_info and record.exc_info[0] is not None:
            kind = record.exc_info[0]
            line["exception_type"] = f"{kind.__module__}.{kind.__qualname__}"
            if line["event"] == "app.crash":
                # Error Reporting groups lines whose message starts with a traceback.
                line["stack_trace"] = self.formatException(record.exc_info)
                line["message"] = line["stack_trace"]
        return json.dumps(line, default=str)
