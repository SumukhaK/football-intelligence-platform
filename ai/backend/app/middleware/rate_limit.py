"""Per-client rate limiting: a safety net against runaway clients (ADR 014).

A sliding one-minute window per client address. Requests over the limit get a
structured 429 with ``Retry-After``. ``/health`` and the docs are never
limited, so monitoring keeps working. State is in memory, which is enough for
the single-process local server this project runs.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

WINDOW_SECONDS = 60.0
EXEMPT_PATHS = frozenset(
    {"/health", "/v1/health", "/v2/health", "/docs", "/redoc", "/openapi.json"}
)


class SlidingWindowLimiter:
    """Counts each key's requests over the last minute."""

    def __init__(
        self, per_minute: int, clock: Callable[[], float] = time.monotonic
    ) -> None:
        """Allow ``per_minute`` requests per key in any 60-second window."""
        self._limit = per_minute
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}

    def check(self, key: str) -> float | None:
        """Record a request; return seconds to wait if it is over the limit."""
        now = self._clock()
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] >= WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= self._limit:
            return WINDOW_SECONDS - (now - hits[0])
        hits.append(now)
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Applies a :class:`SlidingWindowLimiter` to every non-exempt request."""

    def __init__(self, app: ASGIApp, limiter: SlidingWindowLimiter) -> None:
        """Wrap ``app`` with ``limiter``."""
        super().__init__(app)
        self._limiter = limiter

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Reject the request with 429 when its client is over the limit."""
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        wait = self._limiter.check(client)
        if wait is None:
            return await call_next(request)
        seconds = max(1, int(wait + 0.999))
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too many requests",
                "detail": f"Rate limit reached. Try again in {seconds} seconds.",
            },
            headers={"Retry-After": str(seconds)},
        )
