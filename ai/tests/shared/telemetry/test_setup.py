"""Tests for logging setup."""

import logging
from collections.abc import Iterator

import pytest

from shared.telemetry.json_formatter import JsonFormatter
from shared.telemetry.setup import FormatterArgs, configure_logging


def _installed() -> list[logging.Handler]:
    return [
        h
        for h in logging.getLogger().handlers
        if type(h).__name__ == "_TelemetryHandler"
    ]


ARGS: FormatterArgs = {
    "service": "football-api",
    "api_version": "2.0.0",
    "revision": None,
    "gcp_project_id": None,
}


@pytest.fixture(autouse=True)
def _restore_loggers() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    uvicorn = {
        name: (lg.handlers[:], lg.propagate, lg.disabled)
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access")
        for lg in [logging.getLogger(name)]
    }
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    for name, (saved, propagate, disabled) in uvicorn.items():
        lg = logging.getLogger(name)
        lg.handlers[:] = saved
        lg.propagate = propagate
        lg.disabled = disabled


def test_json_mode_installs_the_json_formatter() -> None:
    configure_logging("INFO", "json", ARGS)
    (handler,) = _installed()
    assert isinstance(handler.formatter, JsonFormatter)
    assert logging.getLogger().level == logging.INFO


def test_json_mode_routes_uvicorn_through_the_root_logger() -> None:
    logging.getLogger("uvicorn.error").addHandler(logging.NullHandler())
    configure_logging("INFO", "json", ARGS)
    error = logging.getLogger("uvicorn.error")
    assert error.handlers == []
    assert error.propagate
    # The access log has the raw path and query string, which must not be logged.
    assert logging.getLogger("uvicorn.access").disabled


def test_text_mode_installs_a_plain_formatter() -> None:
    configure_logging("debug", "text", ARGS)
    (handler,) = _installed()
    assert not isinstance(handler.formatter, JsonFormatter)
    assert logging.getLogger().level == logging.DEBUG


def test_text_mode_leaves_uvicorn_alone() -> None:
    marker = logging.NullHandler()
    logging.getLogger("uvicorn.error").addHandler(marker)
    configure_logging("INFO", "text", ARGS)
    assert marker in logging.getLogger("uvicorn.error").handlers


def test_calling_twice_leaves_one_handler() -> None:
    configure_logging("INFO", "json", ARGS)
    configure_logging("INFO", "json", ARGS)
    assert len(_installed()) == 1


def test_other_handlers_are_kept() -> None:
    other = logging.NullHandler()
    logging.getLogger().addHandler(other)
    configure_logging("INFO", "json", ARGS)
    assert other in logging.getLogger().handlers
