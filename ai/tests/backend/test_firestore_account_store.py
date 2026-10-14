"""Tests specific to the Firestore account store (ADR 026)."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.config import Settings
from backend.app.services.account_store import (
    FirestoreAccountStore,
    JsonAccountStore,
    Session,
    User,
    make_account_store,
)
from tests.backend.fake_firestore import FakeFirestore


def _session(token: str, email: str) -> Session:
    return Session(
        token, email, "2026-10-08T12:00:00+00:00", "2026-11-07T12:00:00+00:00"
    )


def test_documents_are_keyed_like_the_json_store() -> None:
    client = FakeFirestore()
    store = FirestoreAccountStore(client)
    store.save_user(User("sam@example.com", "hash", "2026-10-08T12:00:00+00:00"))
    store.save_session(_session("abc123", "sam@example.com"))
    assert set(client.collections["users"]) == {"sam@example.com"}
    assert set(client.collections["sessions"]) == {"abc123"}


def test_a_prefix_keeps_environments_apart() -> None:
    client = FakeFirestore()
    FirestoreAccountStore(client, "staging_").save_session(_session("t", "a@b.c"))
    assert FirestoreAccountStore(client).get_session("t") is None
    assert set(client.collections["staging_sessions"]) == {"t"}


def test_sessions_are_found_by_email() -> None:
    store = FirestoreAccountStore(FakeFirestore())
    store.save_session(_session("t1", "a@b.c"))
    store.save_session(_session("t2", "x@y.z"))
    store.save_session(_session("t3", "a@b.c"))
    assert sorted(s.token_hash for s in store.sessions_for("a@b.c")) == ["t1", "t3"]


def test_a_missing_document_is_none() -> None:
    store = FirestoreAccountStore(FakeFirestore())
    assert store.get_user("nobody@example.com") is None
    assert store.get_invite("nobody@example.com") is None


def test_a_key_with_a_slash_is_refused() -> None:
    store = FirestoreAccountStore(FakeFirestore())
    with pytest.raises(ValueError):
        store.get_user("a/b@example.com")


def test_the_json_store_is_the_default(tmp_path: Path) -> None:
    store = make_account_store(Settings(accounts_path=tmp_path / "a.json"))
    assert isinstance(store, JsonAccountStore)


def test_firestore_is_chosen_by_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, str | None] = {}

    class Client:
        def __init__(self, project: str | None, database: str) -> None:
            seen.update(project=project, database=database)

    monkeypatch.setattr("google.cloud.firestore.Client", Client)
    settings = Settings(account_store="firestore", gcp_project_id="demo")
    assert isinstance(make_account_store(settings), FirestoreAccountStore)
    assert seen == {"project": "demo", "database": "(default)"}
