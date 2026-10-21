"""Invite-only accounts, sessions and consent (ADR 022)."""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from backend.app.consent import CONSENT_VERSION
from backend.app.services.account_store import (
    AccountStore,
    Invite,
    QuestionRecord,
    Session,
    User,
)
from backend.app.services.auth_errors import (
    AccountBlockedError,
    AuthError,
    ConsentRequiredError,
    InvalidCredentialsError,
    InvalidInviteError,
    InviteAlreadyUsedError,
    InviteExpiredError,
    NotSignedInError,
    TooManyAttemptsError,
    WeakPasswordError,
)
from backend.app.services.invite_codes import new_invite_code, normalise_invite_code
from shared.telemetry.context import set_user_ref
from shared.telemetry.events import EventName, emit

# Errors moved to auth_errors.py stay importable from here.
__all__ = [
    "AccountBlockedError",
    "AccountService",
    "AuthError",
    "ConsentRequiredError",
    "INVITE_LIFETIME",
    "InvalidCredentialsError",
    "InvalidInviteError",
    "InviteAlreadyUsedError",
    "InviteExpiredError",
    "LOCKOUT",
    "MAX_FAILED_LOGINS",
    "MAX_STRIKES",
    "MIN_PASSWORD_LENGTH",
    "NewSession",
    "NotSignedInError",
    "QUESTION_LIFETIME",
    "SESSION_LIFETIME",
    "TooManyAttemptsError",
    "WeakPasswordError",
]

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 10
INVITE_LIFETIME = timedelta(days=7)
SESSION_LIFETIME = timedelta(days=30)
MAX_FAILED_LOGINS = 5
LOCKOUT = timedelta(minutes=15)
QUESTION_LIFETIME = timedelta(days=90)
# Harmful questions before a permanent ban (ADR 027).
MAX_STRIKES = 3
_SCRYPT = {"n": 2**14, "r": 8, "p": 1, "dklen": 32}


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
        user_ref: Callable[[str], str] | None = None,
    ) -> None:
        """Initialise with a store, a clock and the hash that names users in logs."""
        self._store = store
        self._clock = clock
        self._user_ref = user_ref

    def _log(self, action: str, outcome: str, email: str | None) -> None:
        """Log ``auth.event``; ``email`` is given only when the account is known."""
        user_ref = None
        if email is not None and self._user_ref is not None:
            user_ref = self._user_ref(email)
        message = f"Account action {action}: {outcome}"
        if user_ref is None:
            emit(logger, EventName.AUTH_EVENT, message, action=action, outcome=outcome)
            return
        emit(
            logger,
            EventName.AUTH_EVENT,
            message,
            action=action,
            outcome=outcome,
            user_ref=user_ref,
        )

    def create_invite(self, email: str) -> str:
        """A one-time code for ``email``; replaces any earlier invite."""
        code = new_invite_code()
        expires = self._clock() + INVITE_LIFETIME
        self._store.save_invite(
            Invite(
                _normalise(email),
                _digest(normalise_invite_code(code)),
                expires.isoformat(),
            )
        )
        return code

    def redeem_invite(self, email: str, code: str, password: str) -> NewSession:
        """Set the password for an invited email and sign in.

        Redeeming again for an existing account resets its password.
        """
        email = _normalise(email)
        try:
            session = self._redeem(email, code, password)
        except AuthError as exc:
            known = self._store.get_user(email) is not None
            self._log("redeem_invite", exc.outcome, email if known else None)
            raise
        self._log("redeem_invite", "ok", email)
        return session

    def _redeem(self, email: str, code: str, password: str) -> NewSession:
        invite = self._store.get_invite(email)
        now = self._clock()
        # Only someone holding the right code learns more than "wrong".
        if invite is None or not _code_matches(invite.code_hash, code):
            raise InvalidInviteError("The invite code is wrong, used or expired.")
        if invite.redeemed_at is not None:
            raise InviteAlreadyUsedError(
                "This code already set up your account. Sign in with the password "
                "you chose, or ask for a new code to reset it."
            )
        if datetime.fromisoformat(invite.expires_at) < now:
            raise InviteExpiredError("This code has expired. Ask for a new one.")
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
        try:
            session = self._login(user, password)
        except AuthError as exc:
            self._log("sign_in", exc.outcome, user.email if user else None)
            raise
        assert user is not None
        self._log("sign_in", "ok", user.email)
        return session

    def _login(self, user: User | None, password: str) -> NewSession:
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
        self._store.update_user(user.email, _clear_failures)
        return self._new_session(user)

    def logout(self, token: str | None) -> None:
        """End the session behind ``token``, if any."""
        session = self._store.get_session(_digest(token)) if token else None
        if session is None:
            self._log("sign_out", NotSignedInError.outcome, None)
            return
        session.revoked = True
        self._store.save_session(session)
        self._log("sign_out", "ok", session.email)

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
        if self._user_ref is not None:
            set_user_ref(self._user_ref(user.email))
        return user

    def record_consent(self, user: User, version: int, store_questions: bool) -> User:
        """Store that ``user`` accepted notice ``version``.

        Raises:
            ConsentRequiredError: ``version`` is not the current notice.
        """
        if version != CONSENT_VERSION:
            self._log("consent", ConsentRequiredError.outcome, user.email)
            raise ConsentRequiredError(
                f"The current notice is version {CONSENT_VERSION}; show it again."
            )
        self._log("consent", "ok", user.email)
        user.consent_version = version
        user.consented_at = self._clock().isoformat()
        user.store_questions = store_questions
        self._store.save_user(user)
        return user

    def record_question(
        self,
        user: User,
        question: str,
        outcome: str,
        model: str,
        conversation_id: str | None,
    ) -> None:
        """Store ``question`` if ``user`` opted in; kept for 90 days (ADR 034)."""
        if not user.store_questions:
            return
        now = self._clock()
        self._store.save_question(
            QuestionRecord(
                email=user.email,
                asked_at=now.isoformat(),
                question=question,
                outcome=outcome,
                model=model,
                conversation_id=conversation_id,
                expires_at=(now + QUESTION_LIFETIME).isoformat(),
            )
        )

    def add_strike(self, email: str) -> User:
        """Count one harmful question against ``email``; the last one bans.

        Raises:
            KeyError: If there is no such user.
        """
        # Counters change atomically in the store, so parallel strikes all count.
        user = self._store.update_user(_normalise(email), _add_strike)
        if user is None:
            raise KeyError(email)
        if user.strikes >= MAX_STRIKES:
            user = self.set_banned(user.email, True)
        self._log("strike", "blocked" if user.status == "banned" else "ok", user.email)
        return user

    def set_banned(self, email: str, banned: bool) -> User:
        """Ban or unban ``email``; a ban ends every session, an unban clears strikes.

        Raises:
            KeyError: If there is no such user.
        """
        user = self._store.get_user(_normalise(email))
        if user is None:
            raise KeyError(email)
        user.status = "banned" if banned else "active"
        if not banned:
            user.strikes = 0
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
        def add_failure(fresh: User) -> None:
            recent = [
                stamp
                for stamp in fresh.failed_logins
                if datetime.fromisoformat(stamp) > now - LOCKOUT
            ]
            recent.append(now.isoformat())
            fresh.failed_logins = recent
            if len(recent) >= MAX_FAILED_LOGINS:
                fresh.locked_until = (now + LOCKOUT).isoformat()

        # Atomic in the store, so parallel wrong passwords all count.
        self._store.update_user(user.email, add_failure)


def _add_strike(user: User) -> None:
    user.strikes += 1


def _clear_failures(user: User) -> None:
    user.failed_logins, user.locked_until = [], None


def _normalise(email: str) -> str:
    return email.strip().lower()


def _digest(secret: str) -> str:
    """SHA-256 of a high-entropy secret (tokens and codes, not passwords)."""
    return hashlib.sha256(secret.encode()).hexdigest()


def _code_matches(code_hash: str, code: str) -> bool:
    """Whether ``code`` is the invite's, typed loosely or (for older codes) exactly.

    Codes sent before the ``XXXX-XXXX`` format were stored as the digest of the
    raw code; they keep working until they expire.
    """
    normalised = hmac.compare_digest(code_hash, _digest(normalise_invite_code(code)))
    raw = hmac.compare_digest(code_hash, _digest(code))
    return normalised or raw


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
