"""Tests for backend.app.services.account_service."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from backend.app.consent import CONSENT_VERSION
from backend.app.services.account_service import (
    AccountBlockedError,
    AccountService,
    ConsentRequiredError,
    InvalidCredentialsError,
    InvalidInviteError,
    NotSignedInError,
    TooManyAttemptsError,
    WeakPasswordError,
)
from backend.app.services.account_store import JsonAccountStore

EMAIL = "Sam@Example.com"
PASSWORD = "correct horse battery"


class Clock:
    """A clock tests can move forward."""

    def __init__(self) -> None:
        self.now = datetime(2026, 10, 8, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture()
def clock() -> Clock:
    return Clock()


@pytest.fixture()
def accounts(tmp_path: Path, clock: Clock) -> AccountService:
    return AccountService(JsonAccountStore(tmp_path / "accounts.json"), clock)


def _signed_up(accounts: AccountService) -> str:
    code = accounts.create_invite(EMAIL)
    return accounts.redeem_invite(EMAIL, code, PASSWORD).token


def test_redeemed_invite_signs_in(accounts: AccountService) -> None:
    """Redeeming an invite creates the account and a working session."""
    token = _signed_up(accounts)
    assert accounts.authenticate(token).email == "sam@example.com"


def test_invite_codes_are_single_use(accounts: AccountService) -> None:
    """A redeemed code cannot be used again."""
    code = accounts.create_invite(EMAIL)
    accounts.redeem_invite(EMAIL, code, PASSWORD)
    with pytest.raises(InvalidInviteError):
        accounts.redeem_invite(EMAIL, code, "another password")


def test_wrong_or_expired_invite_is_refused(
    accounts: AccountService, clock: Clock
) -> None:
    """A wrong code, or one older than 7 days, does not work."""
    code = accounts.create_invite(EMAIL)
    with pytest.raises(InvalidInviteError):
        accounts.redeem_invite(EMAIL, "wrong", PASSWORD)
    clock.now += timedelta(days=8)
    with pytest.raises(InvalidInviteError):
        accounts.redeem_invite(EMAIL, code, PASSWORD)


def test_uninvited_email_cannot_sign_up(accounts: AccountService) -> None:
    """Without an invite there is no way in."""
    with pytest.raises(InvalidInviteError):
        accounts.redeem_invite("stranger@example.com", "anything", PASSWORD)


def test_short_passwords_are_refused(accounts: AccountService) -> None:
    """Passwords need at least 10 characters."""
    code = accounts.create_invite(EMAIL)
    with pytest.raises(WeakPasswordError):
        accounts.redeem_invite(EMAIL, code, "short")


def test_login_checks_the_password(accounts: AccountService) -> None:
    """The right password signs in; a wrong one or an unknown email does not."""
    _signed_up(accounts)
    assert accounts.login("sam@example.com", PASSWORD).token
    with pytest.raises(InvalidCredentialsError):
        accounts.login(EMAIL, "wrong password")
    with pytest.raises(InvalidCredentialsError):
        accounts.login("nobody@example.com", PASSWORD)


def test_repeated_failures_lock_the_email(
    accounts: AccountService, clock: Clock
) -> None:
    """Five failures lock sign-in for 15 minutes, even with the right password."""
    _signed_up(accounts)
    for _ in range(5):
        with pytest.raises(InvalidCredentialsError):
            accounts.login(EMAIL, "wrong password")
    with pytest.raises(TooManyAttemptsError):
        accounts.login(EMAIL, PASSWORD)
    clock.now += timedelta(minutes=16)
    assert accounts.login(EMAIL, PASSWORD).token


def test_sessions_end_on_logout_and_expiry(
    accounts: AccountService, clock: Clock
) -> None:
    """A logged-out or 30-day-old token is no longer accepted."""
    token = _signed_up(accounts)
    accounts.logout(token)
    with pytest.raises(NotSignedInError):
        accounts.authenticate(token)
    token = accounts.login(EMAIL, PASSWORD).token
    clock.now += timedelta(days=31)
    with pytest.raises(NotSignedInError):
        accounts.authenticate(token)


def test_missing_or_unknown_token_is_not_signed_in(accounts: AccountService) -> None:
    """No token, or a made-up one, is refused."""
    for token in (None, "", "made-up"):
        with pytest.raises(NotSignedInError):
            accounts.authenticate(token)


def test_ban_blocks_sessions_and_sign_in(accounts: AccountService) -> None:
    """A ban ends every session and refuses new sign-ins until unbanned."""
    token = _signed_up(accounts)
    accounts.set_banned(EMAIL, banned=True)
    with pytest.raises(NotSignedInError):
        accounts.authenticate(token)
    with pytest.raises(AccountBlockedError):
        accounts.login(EMAIL, PASSWORD)
    accounts.set_banned(EMAIL, banned=False)
    assert accounts.login(EMAIL, PASSWORD).token


def test_new_invite_resets_the_password(accounts: AccountService) -> None:
    """Redeeming a new invite sets a new password and ends old sessions."""
    old_token = _signed_up(accounts)
    code = accounts.create_invite(EMAIL)
    accounts.redeem_invite(EMAIL, code, "a brand new password")
    with pytest.raises(NotSignedInError):
        accounts.authenticate(old_token)
    with pytest.raises(InvalidCredentialsError):
        accounts.login(EMAIL, PASSWORD)


def test_consent_is_recorded(accounts: AccountService, clock: Clock) -> None:
    """Accepting the notice stores the version, time and question opt-in."""
    user = accounts.authenticate(_signed_up(accounts))
    user = accounts.record_consent(user, version=1, store_questions=True)
    assert (user.consent_version, user.store_questions) == (1, True)
    assert user.consented_at == clock.now.isoformat()


def test_secrets_are_never_stored_in_plain_text(
    accounts: AccountService, tmp_path: Path
) -> None:
    """The file holds hashes only: no password, invite code or token."""
    code = accounts.create_invite(EMAIL)
    token = accounts.redeem_invite(EMAIL, code, PASSWORD).token
    stored = (tmp_path / "accounts.json").read_text(encoding="utf-8")
    for secret in (PASSWORD, code, token):
        assert secret not in stored


Events = Callable[[str], list[tuple[str, dict[str, Any]]]]


@pytest.fixture()
def logged(tmp_path: Path, clock: Clock) -> AccountService:
    """Accounts that name users in logs by a test hash."""
    return AccountService(
        JsonAccountStore(tmp_path / "accounts.json"),
        clock,
        user_ref=lambda email: f"ref:{email}",
    )


def _auth(events: Events) -> list[tuple[str, str, str, str | None]]:
    return [
        (severity, a["action"], a["outcome"], a.get("user_ref"))
        for severity, a in events("auth.event")
    ]


def test_sign_up_and_sign_in_are_logged(logged: AccountService, events: Events) -> None:
    token = _signed_up(logged)
    logged.login(EMAIL, PASSWORD)
    logged.logout(token)
    logged.logout(None)
    known = "ref:sam@example.com"
    assert _auth(events) == [
        ("INFO", "redeem_invite", "ok", known),
        ("INFO", "sign_in", "ok", known),
        ("INFO", "sign_out", "ok", known),
        ("INFO", "sign_out", "not_signed_in", None),
    ]


def test_failed_sign_ins_end_in_a_lockout(
    logged: AccountService, events: Events
) -> None:
    _signed_up(logged)
    for _ in range(5):
        with pytest.raises(InvalidCredentialsError):
            logged.login(EMAIL, "wrong password")
    with pytest.raises(TooManyAttemptsError):
        logged.login(EMAIL, PASSWORD)
    with pytest.raises(InvalidCredentialsError):
        logged.login("nobody@example.com", PASSWORD)
    outcomes = [(s, o, r) for s, action, o, r in _auth(events) if action == "sign_in"]
    known = "ref:sam@example.com"
    assert outcomes == [("WARNING", "failed", known)] * 5 + [
        ("WARNING", "locked_out", known),
        ("WARNING", "failed", None),
    ]


def test_refused_invites_and_bans_are_logged(
    logged: AccountService, events: Events
) -> None:
    with pytest.raises(InvalidInviteError):
        logged.redeem_invite("new@example.com", "wrong", PASSWORD)
    code = logged.create_invite("new@example.com")
    with pytest.raises(WeakPasswordError):
        logged.redeem_invite("new@example.com", code, "short")
    _signed_up(logged)
    logged.set_banned(EMAIL, True)
    with pytest.raises(AccountBlockedError):
        logged.login(EMAIL, PASSWORD)
    assert [(a, o, r) for _, a, o, r in _auth(events) if o != "ok"] == [
        ("redeem_invite", "invalid_invite", None),
        ("redeem_invite", "weak_password", None),
        ("sign_in", "blocked", "ref:sam@example.com"),
    ]


def test_consent_is_logged(logged: AccountService, events: Events) -> None:
    _signed_up(logged)
    user = logged.authenticate(logged.login(EMAIL, PASSWORD).token)
    with pytest.raises(ConsentRequiredError):
        logged.record_consent(user, CONSENT_VERSION + 1, False)
    logged.record_consent(user, CONSENT_VERSION, False)
    consent = [(s, o) for s, a, o, _ in _auth(events) if a == "consent"]
    assert consent == [("INFO", "consent_required"), ("INFO", "ok")]


def test_emails_never_reach_the_log(
    logged: AccountService, caplog: pytest.LogCaptureFixture
) -> None:
    _signed_up(logged)
    with pytest.raises(InvalidCredentialsError):
        logged.login(EMAIL, "wrong password")
    assert "example.com" not in caplog.text.lower().replace("ref:sam@example.com", "")
