"""The current request's ID and user_ref, visible to every log line written for it."""

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


class _UserRef:
    """A per-request box for the user_ref.

    Sync dependencies and routes run in the thread pool with a copy of the
    context, so a plain ``ContextVar.set`` there would never reach the
    ``http.request`` line the middleware writes. Mutating a shared box does.
    """

    def __init__(self) -> None:
        self.value: str | None = None


_user_ref: ContextVar[_UserRef | None] = ContextVar("user_ref", default=None)


def start_user_ref() -> Token[_UserRef | None]:
    """Open an empty user_ref slot for one request; reset it with the token."""
    return _user_ref.set(_UserRef())


def reset_user_ref(token: Token[_UserRef | None]) -> None:
    """Close the slot opened by ``start_user_ref``."""
    _user_ref.reset(token)


def set_user_ref(value: str) -> None:
    """Record the signed-in user's ``user_ref``; ignored outside a request."""
    box = _user_ref.get()
    if box is not None:
        box.value = value


def get_user_ref() -> str | None:
    """Return the current request's ``user_ref``, or None if nobody signed in."""
    box = _user_ref.get()
    return None if box is None else box.value
