"""Accept a caller's request ID when it is safe to log, or create one."""

from __future__ import annotations

import re
from collections.abc import Callable
from uuid import uuid4

REQUEST_ID_HEADER = "X-Request-ID"
_VALID = re.compile(r"[A-Za-z0-9._-]{8,64}")


def _new_request_id() -> str:
    return uuid4().hex


def parse_or_create(
    header_value: str | None, factory: Callable[[], str] = _new_request_id
) -> str:
    """Return ``header_value`` if it matches the contract's pattern, else a new ID."""
    if header_value is not None and _VALID.fullmatch(header_value):
        return header_value
    return factory()
