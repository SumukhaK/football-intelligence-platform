"""Tests for backend.app.services.invite_codes and how invites accept codes."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from backend.app.services.account_service import AccountService, InvalidInviteError
from backend.app.services.account_store import Invite, JsonAccountStore
from backend.app.services.invite_codes import (
    INVITE_ALPHABET,
    new_invite_code,
    normalise_invite_code,
)

EMAIL = "sam@example.com"
PASSWORD = "correct horse battery"
NOW = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)


def test_codes_are_two_groups_of_four_from_the_alphabet() -> None:
    pattern = re.compile(f"^[{INVITE_ALPHABET}]{{4}}-[{INVITE_ALPHABET}]{{4}}$")
    codes = {new_invite_code() for _ in range(200)}
    assert all(pattern.match(code) for code in codes)
    assert len(codes) == 200


def test_the_alphabet_leaves_out_lookalikes() -> None:
    assert not set("ILOU01") & set(INVITE_ALPHABET)
    assert len(INVITE_ALPHABET) == 30


@pytest.mark.parametrize(
    "typed", ["K7QM-3XWD", "k7qm3xwd", " k7qm - 3xwd ", "K7QM 3XWD", "k7-qm-3x-wd"]
)
def test_normalising_strips_spaces_and_dashes_and_upper_cases(typed: str) -> None:
    assert normalise_invite_code(typed) == "K7QM3XWD"


def _accounts(tmp_path: Path) -> tuple[AccountService, JsonAccountStore]:
    store = JsonAccountStore(tmp_path / "accounts.json")
    return AccountService(store, lambda: NOW), store


def test_a_loosely_typed_code_redeems(tmp_path: Path) -> None:
    accounts, _ = _accounts(tmp_path)
    code = accounts.create_invite(EMAIL)
    typed = code.lower().replace("-", " ")
    assert accounts.redeem_invite(EMAIL, typed, PASSWORD).token


def test_a_code_from_before_the_new_format_still_redeems(tmp_path: Path) -> None:
    accounts, store = _accounts(tmp_path)
    legacy = "aB3-x_Yz9qLmN0pQrStUvW"
    digest = hashlib.sha256(legacy.encode()).hexdigest()
    expires = (NOW + timedelta(days=3)).isoformat()
    store.save_invite(Invite(EMAIL, digest, expires))
    with pytest.raises(InvalidInviteError):
        accounts.redeem_invite(EMAIL, legacy.upper(), PASSWORD)
    assert accounts.redeem_invite(EMAIL, legacy, PASSWORD).token
