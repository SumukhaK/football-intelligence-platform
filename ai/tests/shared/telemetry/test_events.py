"""Tests for the event catalogue and emit."""

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from shared.telemetry.events import EventName, emit

EVENTS_JSON = (
    Path(__file__).resolve().parents[4]
    / "docs"
    / "observability"
    / "telemetry-events.json"
)
LOGGER = logging.getLogger("tests.telemetry")


def test_event_names_match_the_contract() -> None:
    contract = json.loads(EVENTS_JSON.read_text(encoding="utf-8"))
    assert {name.value for name in EventName} == set(contract["events"])


def _emit_level(
    caplog: pytest.LogCaptureFixture, name: EventName, **attributes: Any
) -> int:
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger=LOGGER.name):
        emit(LOGGER, name, "Something happened", **attributes)
    (record,) = caplog.records
    return record.levelno


@pytest.mark.parametrize(
    ("name", "attributes", "level"),
    [
        (EventName.HTTP_REQUEST, {"status": 200}, logging.INFO),
        (EventName.HTTP_REQUEST, {"status": 404}, logging.WARNING),
        (EventName.HTTP_REQUEST, {"status": 503}, logging.ERROR),
        (EventName.APP_ERROR, {"status": 422}, logging.WARNING),
        (EventName.APP_ERROR, {"status": 500}, logging.ERROR),
        (EventName.APP_CRASH, {}, logging.ERROR),
        (EventName.COMPONENT_LOAD, {"status": "ok"}, logging.INFO),
        (EventName.COMPONENT_LOAD, {"status": "degraded"}, logging.WARNING),
        (EventName.COMPONENT_LOAD, {"status": "failed"}, logging.WARNING),
        (EventName.COMPONENT_DEGRADED, {}, logging.WARNING),
        (EventName.RATELIMIT_REJECTED, {}, logging.WARNING),
        (EventName.AUTH_EVENT, {"outcome": "ok"}, logging.INFO),
        (EventName.AUTH_EVENT, {"outcome": "consent_required"}, logging.INFO),
        (EventName.AUTH_EVENT, {"outcome": "failed"}, logging.WARNING),
        (EventName.AUTH_EVENT, {"outcome": "locked_out"}, logging.WARNING),
        (EventName.AUTH_EVENT, {"outcome": "blocked"}, logging.WARNING),
        (EventName.REFRESH_RUN, {"status": "ok"}, logging.INFO),
        (EventName.REFRESH_RUN, {"status": "failed"}, logging.WARNING),
        (EventName.DATA_FRESHNESS, {}, logging.INFO),
        (EventName.ASSISTANT_ANSWER, {}, logging.INFO),
        (EventName.ASSISTANT_TOOL, {"status": "ok"}, logging.INFO),
        (EventName.ASSISTANT_TOOL, {"status": "error"}, logging.WARNING),
        (EventName.ASSISTANT_ABSTAIN, {}, logging.INFO),
        (EventName.DEPENDENCY_CALL, {"status": "ok"}, logging.INFO),
        (EventName.DEPENDENCY_CALL, {"status": "timeout"}, logging.WARNING),
        (EventName.RETRY, {}, logging.WARNING),
        (EventName.FALLBACK, {}, logging.WARNING),
        (EventName.GUARDRAIL_EVENT, {}, logging.INFO),
    ],
)
def test_emit_uses_the_contract_severity(
    caplog: pytest.LogCaptureFixture,
    name: EventName,
    attributes: dict[str, Any],
    level: int,
) -> None:
    assert _emit_level(caplog, name, **attributes) == level


def test_every_event_has_a_severity(caplog: pytest.LogCaptureFixture) -> None:
    for name in EventName:
        assert _emit_level(caplog, name) in (
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
        )


def test_emit_passes_the_event_and_attributes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger=LOGGER.name):
        emit(LOGGER, EventName.FALLBACK, "Used old data", from_path="a", to_path="b")
    (record,) = caplog.records
    assert record.getMessage() == "Used old data"
    assert record.__dict__["event"] == "fallback"
    assert record.__dict__["attributes"] == {"from_path": "a", "to_path": "b"}


def test_an_explicit_level_wins(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, logger=LOGGER.name):
        emit(LOGGER, EventName.FALLBACK, "Quiet", level=logging.DEBUG)
    assert caplog.records[0].levelno == logging.DEBUG


def test_emit_can_attach_an_exception(caplog: pytest.LogCaptureFixture) -> None:
    error = KeyError("missing")
    with caplog.at_level(logging.ERROR, logger=LOGGER.name):
        emit(LOGGER, EventName.APP_CRASH, "Crashed", exc_info=error, route="/x")
    assert caplog.records[0].exc_info is not None
    assert caplog.records[0].exc_info[1] is error
