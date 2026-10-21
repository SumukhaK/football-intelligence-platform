"""Storage for accounts, invites, sessions and opted-in questions (ADR 022, 034).

``AccountStore`` is the interface. ``JsonAccountStore`` keeps everything in one
JSON file, enough for local use and tests. ``FirestoreAccountStore`` keeps it in
Firestore, which survives Cloud Run restarts and scale to zero (ADR 026).
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from backend.app.config import Settings


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
    favourite: dict[str, str] | None = None


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


@dataclass
class QuestionRecord:
    """One question from a user who opted in to storing them (ADR 034)."""

    email: str
    asked_at: str
    question: str
    outcome: str  # "answered", "refused", "strike" or "banned"
    model: str
    conversation_id: str | None
    expires_at: str


class AccountStore(Protocol):
    """Reads and writes users, invites and sessions."""

    def get_user(self, email: str) -> User | None:
        """The user with ``email``, or None."""
        ...

    def save_user(self, user: User) -> None:
        """Save account fields, preserving the separately updated favourite."""
        ...

    def set_favourite(self, email: str, favourite: dict[str, str]) -> None:
        """Patch only the existing account's favourite."""
        ...

    def update_user(self, email: str, change: Callable[[User], None]) -> User | None:
        """Apply ``change`` to a fresh read and save it atomically; None if absent."""
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

    def save_question(self, record: QuestionRecord) -> None:
        """Add one stored question."""
        ...


class JsonAccountStore:
    """All accounts in one JSON file, rewritten atomically on every change."""

    def __init__(self, path: Path) -> None:
        """Use ``path``; the file is created on the first write."""
        self._path = path
        # Re-entrant: update_user holds it across a read and the write it makes.
        self._lock = threading.RLock()

    def get_user(self, email: str) -> User | None:
        """The user with ``email``, or None."""
        row = self._read()["users"].get(email)
        return _user(row)

    def save_user(self, user: User) -> None:
        """Save account fields without overwriting a newer favourite."""
        self._write("users", user.email, _account_fields(user), merge=True)

    def set_favourite(self, email: str, favourite: dict[str, str]) -> None:
        """Patch only the existing account's favourite under the write lock."""
        self._write("users", email, {"favourite": favourite}, merge=True, existing=True)

    def update_user(self, email: str, change: Callable[[User], None]) -> User | None:
        """Read, change and save ``email`` under the write lock."""
        with self._lock:
            user = self.get_user(email)
            if user is not None:
                change(user)
                self.save_user(user)
            return user

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

    def save_question(self, record: QuestionRecord) -> None:
        """Add one stored question; the JSON store never expires them."""
        self._write("questions", uuid.uuid4().hex, asdict(record))

    def _read(self) -> dict[str, dict[str, dict[str, Any]]]:
        if not self._path.exists():
            return {"users": {}, "invites": {}, "sessions": {}, "questions": {}}
        data: dict[str, dict[str, dict[str, Any]]] = json.loads(
            self._path.read_text(encoding="utf-8")
        )
        return data

    def _write(
        self,
        table: str,
        key: str,
        row: dict[str, Any],
        *,
        merge: bool = False,
        existing: bool = False,
    ) -> None:
        with self._lock:
            data = self._read()
            previous = data.setdefault(table, {}).get(key)
            if existing and previous is None:
                raise KeyError(key)
            if merge:
                row = {**(previous or {}), **row}
            data.setdefault(table, {})[key] = row
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self._path.with_suffix(".tmp")
            temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
            os.replace(temporary, self._path)


class FirestoreAccountStore:
    """Users, invites, sessions and questions as Firestore documents (ADR 026).

    Each kind is a collection keyed like the JSON store: users and invites by
    email, sessions by token hash. ``client`` is a ``firestore.Client``.
    """

    def __init__(self, client: Any, prefix: str = "") -> None:
        """Use ``client``; ``prefix`` keeps staging and prod collections apart."""
        self._client = client
        self._prefix = prefix

    def get_user(self, email: str) -> User | None:
        """The user with ``email``, or None."""
        row = self._get("users", email)
        return _user(row)

    def save_user(self, user: User) -> None:
        """Merge account fields without overwriting a newer favourite."""
        self._collection("users").document(_document_id(user.email)).set(
            _account_fields(user), merge=True
        )

    def set_favourite(self, email: str, favourite: dict[str, str]) -> None:
        """Atomically patch one field without replacing the account document."""
        self._collection("users").document(_document_id(email)).update(
            {"favourite": favourite}
        )

    def update_user(self, email: str, change: Callable[[User], None]) -> User | None:
        """Read, change and save ``email`` in a transaction, retried on conflict."""
        from google.cloud import firestore

        ref = self._collection("users").document(_document_id(email))

        def apply(transaction: Any) -> User | None:
            snapshot = ref.get(transaction=transaction)
            user = _user(snapshot.to_dict() if snapshot.exists else None)
            if user is not None:
                change(user)
                transaction.set(ref, _account_fields(user), merge=True)
            return user

        result: User | None = firestore.transactional(apply)(self._client.transaction())
        return result

    def get_invite(self, email: str) -> Invite | None:
        """The latest invite for ``email``, or None."""
        row = self._get("invites", email)
        return Invite(**row) if row else None

    def save_invite(self, invite: Invite) -> None:
        """Create or replace the invite for its email."""
        self._set("invites", invite.email, asdict(invite))

    def get_session(self, token_hash: str) -> Session | None:
        """The session with ``token_hash``, or None."""
        row = self._get("sessions", token_hash)
        return _session(row) if row else None

    def save_session(self, session: Session) -> None:
        """Create or replace a session."""
        row: dict[str, Any] = asdict(session)
        # A timestamp, so a TTL policy on expires_at deletes ended sessions.
        row["expires_at"] = datetime.fromisoformat(session.expires_at)
        self._set("sessions", session.token_hash, row)

    def sessions_for(self, email: str) -> list[Session]:
        """Every session of ``email``."""
        from google.cloud.firestore_v1.base_query import FieldFilter

        query = self._collection("sessions").where(
            filter=FieldFilter("email", "==", email)
        )
        return [_session(doc.to_dict()) for doc in query.stream()]

    def save_question(self, record: QuestionRecord) -> None:
        """Add one stored question under a random ID."""
        row: dict[str, Any] = asdict(record)
        # A TTL policy only deletes documents whose field is a timestamp.
        row["expires_at"] = datetime.fromisoformat(record.expires_at)
        self._set("questions", uuid.uuid4().hex, row)

    def _collection(self, name: str) -> Any:
        return self._client.collection(self._prefix + name)

    def _get(self, collection: str, key: str) -> dict[str, Any] | None:
        snapshot = self._collection(collection).document(_document_id(key)).get()
        row: dict[str, Any] | None = snapshot.to_dict() if snapshot.exists else None
        return row

    def _set(self, collection: str, key: str, row: dict[str, Any]) -> None:
        self._collection(collection).document(_document_id(key)).set(row)


def _user(row: dict[str, Any] | None) -> User | None:
    """Read known account fields while retaining unknown fields on future writes."""
    if row is None:
        return None
    return User(
        **{field.name: row[field.name] for field in fields(User) if field.name in row}
    )


def _session(row: dict[str, Any]) -> Session:
    """Read a session whose expiry may be a Firestore timestamp or an older string."""
    expires = row["expires_at"]
    if isinstance(expires, datetime):
        row = {**row, "expires_at": expires.isoformat()}
    return Session(**row)


def _account_fields(user: User) -> dict[str, Any]:
    """Authentication writes never own the independently patched favourite."""
    row = asdict(user)
    row.pop("favourite")
    return row


def _document_id(key: str) -> str:
    """``key`` as a Firestore document ID, which may not contain a slash."""
    if "/" in key or key in {"", ".", ".."}:
        raise ValueError("Account keys cannot be used as Firestore document IDs")
    return key


def make_account_store(settings: Settings) -> AccountStore:
    """The store ``ACCOUNT_STORE`` names: the JSON file or Firestore."""
    if settings.account_store == "json":
        return JsonAccountStore(settings.accounts_path)
    from google.cloud import firestore

    client = firestore.Client(
        project=settings.gcp_project_id, database=settings.firestore_database
    )
    return FirestoreAccountStore(client, settings.firestore_collection_prefix)
