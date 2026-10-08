"""Invite-only accounts, sessions and consent (ADR 022)."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from backend.app.services.account_store import (
    AccountStore,
    Invite,
    Session,
    User,
)

MIN_PASSWORD_LENGTH = 10
INVITE_LIFETIME = timedelta(days=7)
SESSION_LIFETIME = timedelta(days=30)
MAX_FAILED_LOGINS = 5
LOCKOUT = timedelta(minutes=15)
_SCRYPT = {"n": 2**14, "r": 8, "p": 1, "dklen": 32}


class AuthError(Exception):
    """An account problem the API reports as ``{"error", "detail"}``."""

    status_code = 400
    error = "Bad request"


class NotSignedInError(AuthError):
    """No valid session token was sent."""

    status_code, error = 401, "Not signed in"


class InvalidCredentialsError(AuthError):
    """Wrong email or password; the message never says which."""

    status_code, error = 401, "Invalid credentials"


class InvalidInviteError(AuthError):
    """The invite code is wrong, used or expired."""

    status_code, error = 400, "Invalid invite"


class WeakPasswordError(AuthError):
    """The chosen password is too short."""

    status_code, error = 422, "Password too short"


class ConsentRequiredError(AuthError):
    """The user has not accepted the current notice."""

    status_code, error = 403, "Consent required"


class AccountBlockedError(AuthError):
    """The user is banned."""

    status_code, error = 403, "Account blocked"


class TooManyAttemptsError(AuthError):
    """Too many failed logins; try again later."""

    status_code, error = 429, "Too many attempts"


@dataclass(frozen=True)
class NewSession:
    """A token to hand to the client, shown once."""

    token: str
    expires_at: datetime


class AccountService:
    """Creates invites, signs people in and records consent."""

    def __init__(
        self,
        store: AccountStore,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        """Initialise with a store and a clock."""
        self._store = store
        self._clock = clock

    def create_invite(self, email: str) -> str:
        """A one-time code for ``email``; replaces any earlier invite."""
        code = secrets.token_urlsafe(16)
        expires = self._clock() + INVITE_LIFETIME
        self._store.save_invite(
            Invite(_normalise(email), _digest(code), expires.isoformat())
        )
        return code

    def redeem_invite(self, email: str, code: str, password: str) -> NewSession:
        """Set the password for an invited email and sign in.

        Redeeming again for an existing account resets its password.
        """
        email = _normalise(email)
        invite = self._store.get_invite(email)
        now = self._clock()
        if (
            invite is None
            or invite.redeemed_at is not None
            or datetime.fromisoformat(invite.expires_at) < now
            or not hmac.compare_digest(invite.code_hash, _digest(code))
        ):
            raise InvalidInviteError("The invite code is wrong, used or expired.")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise WeakPasswordError(f"Use at least {MIN_PASSWORD_LENGTH} characters.")
        user = self._store.get_user(email) or User(email, "", now.isoformat())
        user.password_hash = _hash_password(password)
        user.failed_logins, user.locked_until = [], None
        self._store.save_user(user)
        invite.redeemed_at = now.isoformat()
        self._store.save_invite(invite)
        self.revoke_sessions(email)
        return self._new_session(user)

    def login(self, email: str, password: str) -> NewSession:
        """Sign in with a password; locks the email after repeated failures."""
        user = self._store.get_user(_normalise(email))
        if user is None:
            # Hash anyway, so response time doesn't reveal which emails exist.
            _check_password(password, _DUMMY_HASH)
            raise InvalidCredentialsError("Wrong email or password.")
        now = self._clock()
        if user.locked_until and datetime.fromisoformat(user.locked_until) > now:
            raise TooManyAttemptsError("Too many failed sign-ins. Try again later.")
        if not _check_password(password, user.password_hash):
            self._record_failure(user, now)
            raise InvalidCredentialsError("Wrong email or password.")
        if user.status == "banned":
            raise AccountBlockedError("This account is blocked.")
        user.failed_logins, user.locked_until = [], None
        self._store.save_user(user)
        return self._new_session(user)

    def logout(self, token: str) -> None:
        """End the session behind ``token``, if any."""
        session = self._store.get_session(_digest(token))
        if session is not None:
            session.revoked = True
            self._store.save_session(session)

    def authenticate(self, token: str | None) -> User:
        """The signed-in user behind ``token``.

        Raises:
            NotSignedInError: No token, or an unknown, revoked or expired one.
            AccountBlockedError: The user is banned.
        """
        session = self._store.get_session(_digest(token)) if token else None
        if (
            session is None
            or session.revoked
            or datetime.fromisoformat(session.expires_at) < self._clock()
        ):
            raise NotSignedInError("Sign in to continue.")
        user = self._store.get_user(session.email)
        if user is None:
            raise NotSignedInError("Sign in to continue.")
        if user.status == "banned":
            raise AccountBlockedError("This account is blocked.")
        return user

    def record_consent(self, user: User, version: int, store_questions: bool) -> User:
        """Store that ``user`` accepted notice ``version``."""
        user.consent_version = version
        user.consented_at = self._clock().isoformat()
        user.store_questions = store_questions
        self._store.save_user(user)
        return user

    def set_banned(self, email: str, banned: bool) -> User:
        """Ban or unban ``email``; a ban ends every session.

        Raises:
            KeyError: If there is no such user.
        """
        user = self._store.get_user(_normalise(email))
        if user is None:
            raise KeyError(email)
        user.status = "banned" if banned else "active"
        self._store.save_user(user)
        if banned:
            self.revoke_sessions(user.email)
        return user

    def revoke_sessions(self, email: str) -> None:
        """End every session of ``email``."""
        for session in self._store.sessions_for(_normalise(email)):
            if not session.revoked:
                session.revoked = True
                self._store.save_session(session)

    def _new_session(self, user: User) -> NewSession:
        token = secrets.token_urlsafe(32)
        now = self._clock()
        expires = now + SESSION_LIFETIME
        self._store.save_session(
            Session(_digest(token), user.email, now.isoformat(), expires.isoformat())
        )
        return NewSession(token, expires)

    def _record_failure(self, user: User, now: datetime) -> None:
        recent = [
            stamp
            for stamp in user.failed_logins
            if datetime.fromisoformat(stamp) > now - LOCKOUT
        ]
        recent.append(now.isoformat())
        user.failed_logins = recent
        if len(recent) >= MAX_FAILED_LOGINS:
            user.locked_until = (now + LOCKOUT).isoformat()
        self._store.save_user(user)


def _normalise(email: str) -> str:
    return email.strip().lower()


def _digest(secret: str) -> str:
    """SHA-256 of a high-entropy secret (tokens and codes, not passwords)."""
    return hashlib.sha256(secret.encode()).hexdigest()


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)
    return f"scrypt${salt.hex()}${key.hex()}"


_DUMMY_HASH = _hash_password("not a real password")


def _check_password(password: str, stored: str) -> bool:
    try:
        scheme, salt, key = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), **_SCRYPT)
    return hmac.compare_digest(candidate.hex(), key)
