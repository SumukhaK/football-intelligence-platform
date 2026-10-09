"""Pseudonymous references for users and clients (telemetry contract section 1)."""

from __future__ import annotations

import hashlib
import hmac


def hash_ref(value: str, salt: str) -> str:
    """Return the first 16 hex of HMAC-SHA256 of ``value``, keyed with ``salt``."""
    digest = hmac.new(salt.encode(), value.encode(), hashlib.sha256).hexdigest()
    return digest[:16]
