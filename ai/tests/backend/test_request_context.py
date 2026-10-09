"""Tests for request IDs and the http.request event (ADR 024)."""

from __future__ import annotations

import io
import json
import logging
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.exceptions import unexpected_error_handler
from backend.app.middleware.rate_limit import RateLimitMiddleware, SlidingWindowLimiter
from backend.app.middleware.request_context import RequestContextMiddleware
from shared.telemetry.json_formatter import JsonFormatter

ROUTE_LOGGER = logging.getLogger("tests.request_context.route")
MIDDLEWARE_LOGGER = "backend.app.middleware.request_context"


class StepClock:
    """Each call moves time on by a quarter of a second."""

    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        self.now += 0.25
        return self.now


def _app(limit: int = 100) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(Exception, unexpected_error_handler)

    @app.get("/teams/{team}")
    def team(team: str) -> dict[str, str]:
        ROUTE_LOGGER.info("Inside the route")
        return {"team": team}

    @app.get("/boom")
    def boom() -> dict[str, str]:
        raise RuntimeError("boom")

    app.add_middleware(
        RateLimitMiddleware, limiter=SlidingWindowLimiter(limit), salt="test-salt"
    )
    app.add_middleware(RequestContextMiddleware, clock=StepClock())
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def logs(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """Capture INFO and above from every logger."""
    with caplog.at_level(logging.INFO):
        yield caplog


def _requests(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [
        r.__dict__["attributes"]
        for r in caplog.records
        if getattr(r, "event", None) == "http.request"
    ]


def test_response_has_a_new_request_id() -> None:
    response = _app().get("/teams/arsenal")
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 32
    assert int(request_id, 16) >= 0


def test_a_valid_incoming_id_is_echoed() -> None:
    response = _app().get("/teams/arsenal", headers={"X-Request-ID": "client-123"})
    assert response.headers["X-Request-ID"] == "client-123"


def test_an_invalid_incoming_id_is_replaced() -> None:
    response = _app().get("/teams/arsenal", headers={"X-Request-ID": "bad id!"})
    assert response.headers["X-Request-ID"] != "bad id!"


def test_a_429_has_the_header() -> None:
    client = _app(limit=1)
    client.get("/teams/arsenal")
    response = client.get("/teams/arsenal", headers={"X-Request-ID": "limited-1"})
    assert response.status_code == 429
    assert response.headers["X-Request-ID"] == "limited-1"


def test_a_500_has_the_header_and_its_body_is_unchanged() -> None:
    response = _app().get("/boom", headers={"X-Request-ID": "crashed-1"})
    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "crashed-1"
    assert response.json() == {
        "error": "Internal server error",
        "detail": "An unexpected error occurred.",
    }


def _json_lines(logger: logging.Logger, path: str, request_id: str) -> list[Any]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        JsonFormatter(
            service="football-api",
            api_version="2.0.0",
            revision=None,
            gcp_project_id=None,
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        _app().get(path, headers={"X-Request-ID": request_id})
    finally:
        logger.removeHandler(handler)
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_a_log_line_inside_the_route_carries_the_id() -> None:
    (line,) = _json_lines(ROUTE_LOGGER, "/teams/arsenal", "inside-1")
    assert line["message"] == "Inside the route"
    assert line["request_id"] == "inside-1"


def test_the_500_handler_log_line_carries_the_id() -> None:
    exceptions_logger = logging.getLogger("backend.app.exceptions")
    lines = _json_lines(exceptions_logger, "/boom", "crashed-2")
    (crash,) = [line for line in lines if line["event"] == "app.crash"]
    assert crash["request_id"] == "crashed-2"


def test_one_http_request_event_per_request(logs: pytest.LogCaptureFixture) -> None:
    client = _app()
    client.get("/teams/arsenal?season=2024")
    client.get("/teams/chelsea")
    assert (
        _requests(logs)
        == [
            {
                "method": "GET",
                "route": "/teams/{team}",
                "status": 200,
                "duration_ms": 250,
                "error_code": None,
            }
        ]
        * 2
    )


def test_unmatched_and_failed_requests_are_logged(
    logs: pytest.LogCaptureFixture,
) -> None:
    client = _app()
    client.get("/nowhere")
    client.get("/boom")
    routes = [(r["route"], r["status"]) for r in _requests(logs)]
    assert routes == [("<unmatched>", 404), ("/boom", 500)]


def test_the_event_is_logged_by_the_middleware_logger(
    logs: pytest.LogCaptureFixture,
) -> None:
    _app().get("/teams/arsenal")
    (record,) = [r for r in logs.records if getattr(r, "event", None)]
    assert record.name == MIDDLEWARE_LOGGER
    assert record.levelno == logging.INFO


def test_the_real_app_logs_the_versioned_route_template(
    client: TestClient, logs: pytest.LogCaptureFixture
) -> None:
    response = client.get("/v2/health")
    assert "X-Request-ID" in response.headers
    assert [r["route"] for r in _requests(logs)] == ["/v2/health"]


def test_the_real_app_logs_path_parameters_as_a_template(
    client: TestClient, logs: pytest.LogCaptureFixture
) -> None:
    client.get("/v2/teams/Arsenal/outlook")
    client.get("/v1/health")
    assert [r["route"] for r in _requests(logs)] == [
        "/v2/teams/{team}/outlook",
        "/v1/health",
    ]


def test_a_429_logs_its_error_code(logs: pytest.LogCaptureFixture) -> None:
    client = _app(limit=1)
    client.get("/teams/arsenal")
    client.get("/teams/arsenal")
    assert [r["error_code"] for r in _requests(logs)] == [None, "Too many requests"]


def test_a_crash_logs_its_error_code(logs: pytest.LogCaptureFixture) -> None:
    _app().get("/boom")
    assert [r["error_code"] for r in _requests(logs)] == ["Internal server error"]
