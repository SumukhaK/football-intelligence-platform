"""Per-client rate limiting: a safety net against runaway clients (ADR 014).

A sliding one-minute window per client address. Requests over the limit get a
structured 429 with ``Retry-After``. Health, the probes and the docs are never
limited, so monitoring keeps working. State is in memory, which is enough for
the single-process local server this project runs; idle clients are dropped so
memory stays bounded. Shared state is needed before Cloud Run scales past one instance.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.app.middleware.request_context import UNMATCHED_ROUTE, record_error_code
from shared.telemetry.events import EventName, emit
from shared.telemetry.privacy import hash_ref

logger = logging.getLogger(__name__)
TOO_MANY_REQUESTS = "Too many requests"

WINDOW_SECONDS = 60.0
EXEMPT_PATHS = frozenset(
    {
        "/health",
        "/v1/health",
        "/v2/health",
        "/v2/live",
        "/v2/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
)


# Clients tracked before idle ones are dropped (an O(n) sweep).
SWEEP_AT = 10_000


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
        if len(self._hits) >= SWEEP_AT:
            self._forget_idle(now)
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] >= WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= self._limit:
            return WINDOW_SECONDS - (now - hits[0])
        hits.append(now)
        return None

    def _forget_idle(self, now: float) -> None:
        """Drop keys with no request in the last minute, so memory stays bounded."""
        idle = [k for k, hits in self._hits.items() if now - hits[-1] >= WINDOW_SECONDS]
        for key in idle:
            del self._hits[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Applies a :class:`SlidingWindowLimiter` to every non-exempt request."""

    def __init__(
        self,
        app: ASGIApp,
        limiter: SlidingWindowLimiter,
        salt: str,
        trusted_proxy_hops: int = 0,
    ) -> None:
        """Wrap ``app`` with ``limiter``; ``salt`` keys the logged client hash.

        ``trusted_proxy_hops`` is how many proxies in front of the server add
        to ``X-Forwarded-For`` (see :func:`client_address`).
        """
        super().__init__(app)
        self._limiter = limiter
        self._salt = salt
        self._hops = trusted_proxy_hops

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Reject the request with 429 when its client is over the limit."""
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        client = client_address(request, self._hops)
        wait = self._limiter.check(client)
        if wait is None:
            return await call_next(request)
        seconds = max(1, int(wait + 0.999))
        # The limiter runs before routing, so there is no route template yet.
        emit(
            logger,
            EventName.RATELIMIT_REJECTED,
            "Client is over the rate limit",
            route=UNMATCHED_ROUTE,
            client_ref=hash_ref(client, self._salt),
            retry_after_s=seconds,
        )
        record_error_code(request, TOO_MANY_REQUESTS)
        return JSONResponse(
            status_code=429,
            content={
                "error": TOO_MANY_REQUESTS,
                "detail": f"Rate limit reached. Try again in {seconds} seconds.",
            },
            headers={"Retry-After": str(seconds)},
        )


def client_address(request: Request, trusted_proxy_hops: int) -> str:
    """The caller's address, read past ``trusted_proxy_hops`` trusted proxies.

    Each proxy appends the address it saw to ``X-Forwarded-For``, so the entry
    that many places from the end was written by the outermost trusted proxy.
    Entries further left came from the client and could be forged. With no
    trusted proxies, the socket's peer address is used.
    """
    peer = request.client.host if request.client else "unknown"
    if trusted_proxy_hops == 0:
        return peer
    header = request.headers.get("x-forwarded-for", "")
    forwarded = [part.strip() for part in header.split(",") if part.strip()]
    if len(forwarded) < trusted_proxy_hops:
        return peer
    return forwarded[-trusted_proxy_hops]
