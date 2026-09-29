"""Tests for the per-client rate limiter (ADR 014)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.middleware.rate_limit import RateLimitMiddleware, SlidingWindowLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_the_limit_then_waits() -> None:
    clock = FakeClock()
    limiter = SlidingWindowLimiter(per_minute=3, clock=clock)
    assert [limiter.check("a") for _ in range(3)] == [None, None, None]
    wait = limiter.check("a")
    assert wait is not None and 59 < wait <= 60


def test_window_slides() -> None:
    clock = FakeClock()
    limiter = SlidingWindowLimiter(per_minute=1, clock=clock)
    assert limiter.check("a") is None
    clock.now += 30
    assert limiter.check("a") is not None
    clock.now += 31
    assert limiter.check("a") is None


def test_clients_are_counted_separately() -> None:
    limiter = SlidingWindowLimiter(per_minute=1, clock=FakeClock())
    assert limiter.check("a") is None
    assert limiter.check("b") is None


def _app(limit: int) -> TestClient:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limiter=SlidingWindowLimiter(limit))

    @app.get("/v2/teams")
    def teams() -> dict[str, str]:
        return {"ok": "yes"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(app)


def test_over_the_limit_is_a_structured_429() -> None:
    client = _app(limit=2)
    assert client.get("/v2/teams").status_code == 200
    assert client.get("/v2/teams").status_code == 200
    response = client.get("/v2/teams")
    assert response.status_code == 429
    assert response.json()["error"] == "Too many requests"
    assert int(response.headers["Retry-After"]) >= 1


def test_health_is_never_limited() -> None:
    client = _app(limit=1)
    assert all(client.get("/health").status_code == 200 for _ in range(5))
