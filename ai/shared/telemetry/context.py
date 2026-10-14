"""The current request's ID, visible to every log line written while handling it."""

from __future__ import annotations

from contextvars import ContextVar, Token

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Return the current request's ID, or None outside a request."""
    return _request_id.get()


def set_request_id(value: str) -> Token[str | None]:
    """Make ``value`` the current request's ID; reset it with the returned token."""
    return _request_id.set(value)


def reset_request_id(token: Token[str | None]) -> None:
    """Restore the request ID that was current before ``set_request_id``."""
    _request_id.reset(token)
