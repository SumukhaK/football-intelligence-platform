"""Tests for the JSON log formatter."""

import json
import logging
import sys
from typing import Any

from shared.telemetry.context import reset_request_id, set_request_id
from shared.telemetry.json_formatter import COMMON_FIELDS, JsonFormatter

FORMATTER = JsonFormatter(
    service="football-api",
    api_version="2.0.0",
    revision="rev-1",
    gcp_project_id=None,
)


def _record(**extra: Any) -> logging.LogRecord:
    record = logging.LogRecord(
        "backend.app.main", logging.WARNING, __file__, 1, "Hello %s", ("you",), None
    )
    record.created = 1791535947.1234
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def _format(record: logging.LogRecord) -> dict[str, Any]:
    line = FORMATTER.format(record)
    assert "\n" not in line
    data: dict[str, Any] = json.loads(line)
    return data


def test_every_common_field_is_present() -> None:
    data = _format(_record())
    assert list(data) == list(COMMON_FIELDS)
    assert data["timestamp"] == "2026-10-09T08:52:27.123Z"
    assert data["severity"] == "WARNING"
    assert data["message"] == "Hello you"
    assert data["logger"] == "backend.app.main"
    assert data["service"] == "football-api"
    assert data["revision"] == "rev-1"
    assert data["api_version"] == "2.0.0"
    assert data["contract_version"] == "1.0.0"
    assert data["event"] is None
    assert data["attributes"] == {}
    assert data["request_id"] is None
    assert data["trace_id"] is None
    assert data["logging.googleapis.com/trace"] is None
    assert data["logging.googleapis.com/spanId"] is None


def test_event_and_attributes_come_from_extra() -> None:
    data = _format(_record(event="http.request", attributes={"status": 200}))
    assert data["event"] == "http.request"
    assert data["attributes"] == {"status": 200}


def test_request_id_comes_from_the_context() -> None:
    token = set_request_id("req-12345678")
    try:
        data = _format(_record())
    finally:
        reset_request_id(token)
    assert data["request_id"] == "req-12345678"


def test_exception_fields_are_added() -> None:
    try:
        raise KeyError("missing")
    except KeyError:
        record = _record(exc_info=sys.exc_info())
    data = _format(record)
    assert data["exception_type"] == "builtins.KeyError"
    assert "KeyError: 'missing'" in data["stack_trace"]


def test_lines_without_exceptions_have_no_exception_fields() -> None:
    data = _format(_record())
    assert "exception_type" not in data
    assert "stack_trace" not in data


def test_unserialisable_attribute_values_become_strings() -> None:
    data = _format(_record(attributes={"value": object}))
    assert data["attributes"]["value"] == str(object)
