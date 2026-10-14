"""Tests for pseudonymous references."""

import hashlib
import hmac

from shared.telemetry.privacy import hash_ref


def test_is_the_first_16_hex_of_the_hmac() -> None:
    expected = hmac.new(b"salt", b"203.0.113.9", hashlib.sha256).hexdigest()[:16]
    assert hash_ref("203.0.113.9", "salt") == expected


def test_depends_on_the_salt() -> None:
    assert hash_ref("a@example.com", "one") != hash_ref("a@example.com", "two")


def test_never_contains_the_value() -> None:
    assert "example" not in hash_ref("a@example.com", "salt")
