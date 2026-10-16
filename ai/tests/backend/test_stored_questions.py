"""Tests for storing opted-in question text (ADR 034)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from backend.app.consent import CONSENT_VERSION
from backend.app.schemas.assistant import ChatRequest
from backend.app.services.account_service import AccountService
from backend.app.services.account_store import (
    AccountStore,
    FirestoreAccountStore,
    JsonAccountStore,
    User,
)
from backend.app.services.chat_service import ChatService
from tests.backend.fake_firestore import FakeFirestore

EMAIL = "sam@example.com"
NOW = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)
QUESTION = ChatRequest(message="Who wins at Anfield?", conversation_id="conv-0001")


class Stored:
    """A store plus a way to read back what it saved as questions."""

    def __init__(self, kind: str, tmp_path: Path) -> None:
        self._path = tmp_path / "accounts.json"
        self._firestore = FakeFirestore()
        self.store: AccountStore = (
            JsonAccountStore(self._path)
            if kind == "json"
            else FirestoreAccountStore(self._firestore, "staging_")
        )

    def questions(self) -> list[dict[str, Any]]:
        if isinstance(self.store, JsonAccountStore):
            if not self._path.exists():
                return []
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return list(data.get("questions", {}).values())
        return list(self._firestore.collections.get("staging_questions", {}).values())


@pytest.fixture(params=["json", "firestore"])
def stored(request: pytest.FixtureRequest, tmp_path: Path) -> Stored:
    return Stored(request.param, tmp_path)


def _signed_up(stored: Stored, opted_in: bool) -> tuple[AccountService, User]:
    accounts = AccountService(stored.store, lambda: NOW)
    accounts.redeem_invite(EMAIL, accounts.create_invite(EMAIL), "correct horse b")
    user = stored.store.get_user(EMAIL)
    assert user is not None
    return accounts, accounts.record_consent(user, CONSENT_VERSION, opted_in)


def _assistant() -> MagicMock:
    assistant = MagicMock()
    assistant.chat.return_value = MagicMock(
        answer="Liverpool 55%.", confidence=0.9, model="m-1", retrieved_count=2
    )
    return assistant


def _safety(categories: list[str]) -> MagicMock:
    safety = MagicMock()
    safety.harmful_categories.return_value = categories
    return safety


def test_an_opted_in_answer_is_stored_without_the_answer(stored: Stored) -> None:
    accounts, user = _signed_up(stored, opted_in=True)
    ChatService(_assistant(), accounts=accounts).chat(QUESTION, user)
    (row,) = stored.questions()
    expires = row["expires_at"]
    if isinstance(expires, datetime):  # Firestore keeps a timestamp for its TTL
        expires = expires.isoformat()
    assert {**row, "expires_at": expires} == {
        "email": EMAIL,
        "asked_at": "2026-10-16T12:00:00+00:00",
        "question": "Who wins at Anfield?",
        "outcome": "answered",
        "model": "m-1",
        "conversation_id": "conv-0001",
        "expires_at": "2027-01-14T12:00:00+00:00",
    }


def test_refusals_are_stored_with_their_outcome(stored: Stored) -> None:
    accounts, user = _signed_up(stored, opted_in=True)
    service = ChatService(_assistant(), _safety(["S1"]), accounts)
    for _ in range(3):
        service.chat(QUESTION, user)
    outcomes = [(r["outcome"], r["model"]) for r in stored.questions()]
    assert outcomes == [("strike", "safety")] * 2 + [("banned", "safety")]


def test_nothing_is_stored_without_the_opt_in(stored: Stored) -> None:
    accounts, user = _signed_up(stored, opted_in=False)
    service = ChatService(_assistant(), accounts=accounts)
    service.chat(QUESTION, user)
    service.chat(QUESTION)
    assert stored.questions() == []


def test_opting_out_stops_later_saves(stored: Stored) -> None:
    accounts, user = _signed_up(stored, opted_in=True)
    service = ChatService(_assistant(), accounts=accounts)
    service.chat(QUESTION, user)
    user = accounts.record_consent(user, CONSENT_VERSION, False)
    service.chat(QUESTION, user)
    assert len(stored.questions()) == 1


def test_a_failed_save_never_fails_the_chat(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    accounts, user = _signed_up(Stored("json", tmp_path), opted_in=True)
    broken = MagicMock(wraps=accounts)
    broken.record_question.side_effect = OSError("disk full")
    with caplog.at_level(logging.WARNING):
        response = ChatService(_assistant(), accounts=broken).chat(QUESTION, user)
    assert response.answer == "Liverpool 55%."
    (record,) = [r for r in caplog.records if getattr(r, "event", None) == "fallback"]
    assert record.__dict__["attributes"] == {
        "from_path": "store_question",
        "to_path": "question_not_stored",
        "cause": "OSError",
    }
    assert "Anfield" not in caplog.text
