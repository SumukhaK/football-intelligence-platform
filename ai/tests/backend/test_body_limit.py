"""Tests for the request body size limit."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.app.middleware.body_limit import BodyLimitMiddleware


def _client(max_bytes: int = 10) -> TestClient:
    app = FastAPI()
    app.add_middleware(BodyLimitMiddleware, max_bytes=max_bytes)

    @app.post("/echo")
    async def echo(request: Request) -> dict[str, int]:
        return {"bytes": len(await request.body())}

    return TestClient(app)


def test_a_body_within_the_limit_is_passed_on() -> None:
    response = _client().post("/echo", content=b"0123456789")
    assert response.status_code == 200
    assert response.json() == {"bytes": 10}


def test_a_body_over_the_limit_is_a_structured_413() -> None:
    response = _client().post("/echo", content=b"0123456789!")
    assert response.status_code == 413
    assert response.json()["error"] == "Request too large"


def test_a_chunked_body_must_declare_its_length() -> None:
    def chunks() -> Iterator[bytes]:
        yield b"012"

    response = _client().post("/echo", content=chunks())
    assert response.status_code == 411
    assert response.json()["error"] == "Length required"


def test_a_request_without_a_body_is_passed_on() -> None:
    app = FastAPI()
    app.add_middleware(BodyLimitMiddleware, max_bytes=1)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"ok": "yes"}

    assert TestClient(app).get("/ping").status_code == 200


def test_the_api_limits_bodies(client: TestClient) -> None:
    response = client.post("/v2/predict", content=b"x" * 20_000)
    assert response.status_code == 413
