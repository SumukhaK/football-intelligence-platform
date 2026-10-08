"""Storage for accounts, invites and sessions (ADR 022).

``AccountStore`` is the interface; ``JsonAccountStore`` keeps everything in one
JSON file, enough for local use, tests and a single-instance staging service.
A Firestore store follows with the hosting tracker's cloud storage step.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class User:
    """One person allowed to use the app."""

    email: str
    password_hash: str
    created_at: str
    status: str = "active"  # "active" or "banned"
    strikes: int = 0
    consent_version: int | None = None
    consented_at: str | None = None
    store_questions: bool = False
    failed_logins: list[str] = field(default_factory=list)
    locked_until: str | None = None


@dataclass
class Invite:
    """A one-time code that lets ``email`` set a password."""

    email: str
    code_hash: str
    expires_at: str
    redeemed_at: str | None = None


@dataclass
class Session:
    """A signed-in device; only the token's hash is stored."""

    token_hash: str
    email: str
    created_at: str
    expires_at: str
    revoked: bool = False


class AccountStore(Protocol):
    """Reads and writes users, invites and sessions."""

    def get_user(self, email: str) -> User | None:
        """The user with ``email``, or None."""
        ...

    def save_user(self, user: User) -> None:
        """Create or replace a user."""
        ...

    def get_invite(self, email: str) -> Invite | None:
        """The latest invite for ``email``, or None."""
        ...

    def save_invite(self, invite: Invite) -> None:
        """Create or replace the invite for its email."""
        ...

    def get_session(self, token_hash: str) -> Session | None:
        """The session with ``token_hash``, or None."""
        ...

    def save_session(self, session: Session) -> None:
        """Create or replace a session."""
        ...

    def sessions_for(self, email: str) -> list[Session]:
        """Every session of ``email``."""
        ...


class JsonAccountStore:
    """All accounts in one JSON file, rewritten atomically on every change."""

    def __init__(self, path: Path) -> None:
        """Use ``path``; the file is created on the first write."""
        self._path = path
        self._lock = threading.Lock()

    def get_user(self, email: str) -> User | None:
        """The user with ``email``, or None."""
        row = self._read()["users"].get(email)
        return User(**row) if row else None

    def save_user(self, user: User) -> None:
        """Create or replace a user."""
        self._write("users", user.email, asdict(user))

    def get_invite(self, email: str) -> Invite | None:
        """The latest invite for ``email``, or None."""
        row = self._read()["invites"].get(email)
        return Invite(**row) if row else None

    def save_invite(self, invite: Invite) -> None:
        """Create or replace the invite for its email."""
        self._write("invites", invite.email, asdict(invite))

    def get_session(self, token_hash: str) -> Session | None:
        """The session with ``token_hash``, or None."""
        row = self._read()["sessions"].get(token_hash)
        return Session(**row) if row else None

    def save_session(self, session: Session) -> None:
        """Create or replace a session."""
        self._write("sessions", session.token_hash, asdict(session))

    def sessions_for(self, email: str) -> list[Session]:
        """Every session of ``email``."""
        rows = self._read()["sessions"].values()
        return [Session(**row) for row in rows if row["email"] == email]

    def _read(self) -> dict[str, dict[str, dict[str, Any]]]:
        if not self._path.exists():
            return {"users": {}, "invites": {}, "sessions": {}}
        data: dict[str, dict[str, dict[str, Any]]] = json.loads(
            self._path.read_text(encoding="utf-8")
        )
        return data

    def _write(self, table: str, key: str, row: dict[str, Any]) -> None:
        with self._lock:
            data = self._read()
            data[table][key] = row
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self._path.with_suffix(".tmp")
            temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
            os.replace(temporary, self._path)
