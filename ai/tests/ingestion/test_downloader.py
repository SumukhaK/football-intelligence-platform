"""Tests for HttpxTransport retries and classify_httpx_error."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
import pytest

from config.settings import Settings
from ingestion.downloader import HttpxTransport, classify_httpx_error
from shared.exceptions import IngestionError
from shared.telemetry.retry import AttemptOutcome, RetryPolicy

_URL = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"
_REQUEST = httpx.Request("GET", _URL)
Events = Callable[[str], list[tuple[str, dict[str, Any]]]]


def _status_error(code: int, headers: dict[str, str] | None = None) -> Exception:
    response = httpx.Response(code, headers=headers, request=_REQUEST)
    return httpx.HTTPStatusError("failed", request=_REQUEST, response=response)


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (httpx.ReadTimeout("slow"), AttemptOutcome("timeout", retryable=True)),
        (httpx.ConnectError("down"), AttemptOutcome("connection_error", None, True)),
        (
            httpx.RemoteProtocolError("bad"),
            AttemptOutcome("connection_error", None, True),
        ),
        (
            _status_error(429, {"Retry-After": "3"}),
            AttemptOutcome("http_error", 429, True, 3.0),
        ),
        (_status_error(429), AttemptOutcome("http_error", 429, True)),
        (
            _status_error(429, {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}),
            AttemptOutcome("http_error", 429, True),
        ),
        (_status_error(500), AttemptOutcome("http_error", 500, True)),
        (_status_error(502), AttemptOutcome("http_error", 502, True)),
        (_status_error(503), AttemptOutcome("http_error", 503, True)),
        (_status_error(504), AttemptOutcome("http_error", 504, True)),
        (_status_error(404), AttemptOutcome("http_error", 404, False)),
        (httpx.TooManyRedirects("loop"), AttemptOutcome("error")),
        (ValueError("other"), AttemptOutcome("error")),
    ],
)
def test_classify_httpx_error(exc: Exception, expected: AttemptOutcome) -> None:
    assert classify_httpx_error(exc) == expected


def _transport(
    *responses: httpx.Response | Exception,
) -> tuple[HttpxTransport, list[float]]:
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    waits: list[float] = []
    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = HttpxTransport(
        "football_data", RetryPolicy(max_attempts=3), client.get, waits.append
    )
    return transport, waits


def test_get_retries_a_503_then_succeeds(events: Events) -> None:
    transport, waits = _transport(
        httpx.Response(503), httpx.Response(200, content=b"csv")
    )
    assert transport.get(_URL, timeout=5) == b"csv"
    assert len(waits) == 1
    calls = events("dependency.call")
    assert [(a["status"], a["http_status"]) for _, a in calls] == [
        ("http_error", 503),
        ("ok", None),
    ]
    ((_, retry),) = events("retry")
    assert (retry["dependency"], retry["cause"]) == ("football_data", "http_503")


def test_two_timeouts_then_success_returns_the_data(events: Events) -> None:
    timeout = httpx.ReadTimeout("slow", request=_REQUEST)
    transport, waits = _transport(timeout, timeout, httpx.Response(200, content=b"csv"))
    assert transport.get(_URL, timeout=5) == b"csv"
    assert len(waits) == 2
    assert len(events("dependency.call")) == 3
    assert len(events("retry")) == 2


def test_429_honours_retry_after() -> None:
    transport, waits = _transport(
        httpx.Response(429, headers={"Retry-After": "2"}), httpx.Response(200)
    )
    transport.get(_URL, timeout=5)
    assert waits == [2.0]


def test_404_is_not_retried_and_keeps_the_error_message() -> None:
    transport, waits = _transport(httpx.Response(404))
    with pytest.raises(IngestionError, match=r"^\[.*E0\.csv\] HTTP 404: Not Found$"):
        transport.get(_URL, timeout=5)
    assert waits == []


def test_final_failure_raises_ingestion_error() -> None:
    error = httpx.ConnectError("down", request=_REQUEST)
    transport, waits = _transport(error, error, error)
    with pytest.raises(IngestionError, match=r"Request failed: down$"):
        transport.get(_URL, timeout=5)
    assert len(waits) == 2


def test_default_policy_comes_from_http_max_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ingestion.downloader.get_settings", lambda: Settings(http_max_retries=1)
    )
    sent: list[str] = []

    def send(url: str, **kwargs: Any) -> httpx.Response:
        sent.append(url)
        return httpx.Response(503, request=_REQUEST)

    transport = HttpxTransport("football_data", send=send, sleep=lambda _: None)
    with pytest.raises(IngestionError, match="HTTP 503"):
        transport.get(_URL, timeout=5)
    assert len(sent) == 2
