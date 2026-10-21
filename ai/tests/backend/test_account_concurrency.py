"""Parallel requests must not lose failed sign-ins or strikes."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from backend.app.services.account_service import (
    AccountService,
    InvalidCredentialsError,
    TooManyAttemptsError,
)
from backend.app.services.account_store import JsonAccountStore, User

EMAIL = "sam@example.com"
PASSWORD = "correct horse battery"


class SlowStore(JsonAccountStore):
    """Reads take a moment, like Firestore, so parallel requests overlap."""

    def get_user(self, email: str) -> User | None:
        """Return the user after a short pause."""
        user = super().get_user(email)
        time.sleep(0.05)
        return user


@pytest.fixture()
def accounts(tmp_path: Path) -> AccountService:
    service = AccountService(SlowStore(tmp_path / "accounts.json"))
    code = service.create_invite(EMAIL)
    service.redeem_invite(EMAIL, code, PASSWORD)
    return service


def _in_parallel(count: int, action: object) -> None:
    start = threading.Barrier(count)

    def run() -> None:
        start.wait()
        action()  # type: ignore[operator]

    with ThreadPoolExecutor(count) as pool:
        for future in [pool.submit(run) for _ in range(count)]:
            future.exception()


def test_parallel_wrong_passwords_all_count(accounts: AccountService) -> None:
    """Five wrong passwords at once still lock the email."""

    def wrong() -> None:
        with pytest.raises(InvalidCredentialsError):
            accounts.login(EMAIL, "wrong password")

    _in_parallel(5, wrong)
    with pytest.raises(TooManyAttemptsError):
        accounts.login(EMAIL, PASSWORD)


def test_parallel_strikes_all_count(accounts: AccountService) -> None:
    """Three harmful questions at once still ban the account (ADR 027)."""
    _in_parallel(3, lambda: accounts.add_strike(EMAIL))
    user = accounts._store.get_user(EMAIL)  # noqa: SLF001
    assert user is not None
    assert user.strikes == 3
    assert user.status == "banned"
