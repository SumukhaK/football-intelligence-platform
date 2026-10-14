"""Rejects request bodies over a size limit before any route reads them.

Every body this API accepts is a small JSON object, so a large one is either a
mistake or an attempt to use up memory. A body must declare its size: a
``Content-Length`` over the limit gets 413, and a body sent without one
(chunked) gets 411, so the limit cannot be dodged by streaming.
"""

from __future__ import annotations

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

TOO_LARGE = "Request too large"
LENGTH_REQUIRED = "Length required"


class BodyLimitMiddleware:
    """Answers 413 or 411 instead of passing an oversized body on."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        """Wrap ``app``; bodies over ``max_bytes`` are refused."""
        self._app = app
        self._max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Check the declared body size, then hand the request on."""
        if scope["type"] == "http":
            refusal = self._refusal(Headers(scope=scope))
            if refusal is not None:
                await refusal(scope, receive, send)
                return
        await self._app(scope, receive, send)

    def _refusal(self, headers: Headers) -> JSONResponse | None:
        length = headers.get("content-length")
        if length is None:
            if "chunked" in headers.get("transfer-encoding", "").lower():
                detail = "Send the body with a Content-Length header."
                return _error(411, LENGTH_REQUIRED, detail)
            return None
        if not length.isdigit() or int(length) > self._max_bytes:
            detail = f"Bodies are limited to {self._max_bytes} bytes."
            return _error(413, TOO_LARGE, detail)
        return None


def _error(status: int, error: str, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": error, "detail": detail})
