"""Tests for request ID parsing."""

import pytest

from shared.telemetry.request_id import parse_or_create


def _new() -> str:
    return "new-id"


def test_valid_header_is_kept() -> None:
    assert parse_or_create("abc.DEF_123-xyz", _new) == "abc.DEF_123-xyz"


def test_boundary_lengths_are_kept() -> None:
    assert parse_or_create("a" * 8, _new) == "a" * 8
    assert parse_or_create("a" * 64, _new) == "a" * 64


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "short",
        "a" * 65,
        "has space1",
        "bad/chars",
        "semi;colon1",
        "ab\n12345",
    ],
)
def test_invalid_or_missing_header_creates_a_new_id(value: str | None) -> None:
    assert parse_or_create(value, _new) == "new-id"


def test_default_factory_makes_32_hex_characters() -> None:
    created = parse_or_create(None)
    assert len(created) == 32
    assert all(c in "0123456789abcdef" for c in created)
