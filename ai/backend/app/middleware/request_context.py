"""Give every request an ID and log one ``http.request`` event for it (ADR 024).

A pure ASGI middleware rather than ``BaseHTTPMiddleware``: that one runs the
app in a separate task, so a context variable set here would not reliably be
visible inside routes and exception handlers.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from shared.telemetry.context import reset_request_id, set_request_id
from shared.telemetry.events import EventName, emit
from shared.telemetry.request_id import REQUEST_ID_HEADER, parse_or_create

logger = logging.getLogger(__name__)
UNMATCHED_ROUTE = "<unmatched>"


def route_template(scope: Scope) -> str:
    """Return the matched route's template, never the raw path."""
    # FastAPI includes routers lazily, so scope["route"] is the route as the
    # router declared it, without the /v1 or /v2 prefix. The prefixed template
    # is only on FastAPI's effective route context; the real-app test guards it.
    effective = scope.get("fastapi", {}).get("effective_route_context")
    for candidate in (effective, scope.get("route")):
        path = getattr(candidate, "path", None)
        if isinstance(path, str) and path:
            return path
    return UNMATCHED_ROUTE


class RequestContextMiddleware:
    """Sets the request ID, returns it in ``X-Request-ID`` and logs the request."""

    def __init__(
        self, app: ASGIApp, clock: Callable[[], float] = time.monotonic
    ) -> None:
        """Wrap ``app``; ``clock`` is a monotonic clock in seconds."""
        self._app = app
        self._clock = clock

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle one ASGI call."""
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        request_id = parse_or_create(Headers(scope=scope).get(REQUEST_ID_HEADER))
        token = set_request_id(request_id)
        started = self._clock()
        status = 500

        async def send_with_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message).append(REQUEST_ID_HEADER, request_id)
            await send(message)

        try:
            await self._app(scope, receive, send_with_id)
        except Exception:
            self._log_request(scope, 500, started)
            # The request ID stays set: Starlette's catch-all 500 handler runs
            # outside this middleware and needs it for its log line and header.
            raise
        self._log_request(scope, status, started)
        reset_request_id(token)

    def _log_request(self, scope: Scope, status: int, started: float) -> None:
        emit(
            logger,
            EventName.HTTP_REQUEST,
            "Request handled",
            method=scope["method"],
            route=route_template(scope),
            status=status,
            duration_ms=round((self._clock() - started) * 1000),
            error_code=None,
        )
