"""Tests for the safety check and strikes in ChatService (ADR 027)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from backend.app.exceptions import AssistantNotAvailableError
from backend.app.schemas.assistant import ChatRequest
from backend.app.services.account_service import AccountService
from backend.app.services.account_store import JsonAccountStore, User
from backend.app.services.chat_service import ChatService

EMAIL = "sam@example.com"
HARMFUL = ChatRequest(message="How do I hurt the referee?")


@pytest.fixture()
def accounts(tmp_path: Path) -> AccountService:
    service = AccountService(JsonAccountStore(tmp_path / "accounts.json"))
    code = service.create_invite(EMAIL)
    service.redeem_invite(EMAIL, code, "correct horse battery")
    return service


def _safety(categories: list[str]) -> MagicMock:
    safety = MagicMock()
    safety.harmful_categories.return_value = categories
    return safety


def _user(accounts: AccountService) -> User:
    user = accounts._store.get_user(EMAIL)  # noqa: SLF001
    assert user is not None
    return user


def test_harmful_question_is_refused_without_the_model(
    accounts: AccountService,
) -> None:
    assistant = MagicMock()
    service = ChatService(assistant, _safety(["S1"]), accounts)
    response = service.chat(HARMFUL, _user(accounts))
    assert response.model == "safety"
    assert response.sources == []
    assert "1 of 3" in response.answer
    assistant.chat.assert_not_called()
    assert _user(accounts).strikes == 1


def test_third_strike_bans_and_ends_sessions(accounts: AccountService) -> None:
    token = accounts.login(EMAIL, "correct horse battery").token
    service = ChatService(MagicMock(), _safety(["S10"]), accounts)
    for _ in range(3):
        response = service.chat(HARMFUL, _user(accounts))
    assert "now blocked" in response.answer
    assert _user(accounts).status == "banned"
    with pytest.raises(Exception, match="Sign in"):
        accounts.authenticate(token)


def test_unban_clears_strikes(accounts: AccountService) -> None:
    service = ChatService(MagicMock(), _safety(["S1"]), accounts)
    for _ in range(3):
        service.chat(HARMFUL, _user(accounts))
    assert accounts.set_banned(EMAIL, False).strikes == 0


def test_signed_out_question_is_refused_without_a_strike() -> None:
    response = ChatService(MagicMock(), _safety(["S1"])).chat(HARMFUL)
    assert response.answer == "I can't help with that question."


def test_safe_question_reaches_the_assistant(accounts: AccountService) -> None:
    assistant = MagicMock()
    assistant.chat.return_value = MagicMock(
        answer="Chelsea 52%.", sources=[], confidence=0.9, model="m", retrieved_count=0
    )
    service = ChatService(assistant, _safety([]), accounts)
    assert service.chat(HARMFUL, _user(accounts)).answer == "Chelsea 52%."
    assert _user(accounts).strikes == 0


def test_unavailable_safety_check_fails_closed(accounts: AccountService) -> None:
    safety = MagicMock()
    safety.harmful_categories.side_effect = RuntimeError("guard down")
    assistant = MagicMock()
    with pytest.raises(AssistantNotAvailableError):
        ChatService(assistant, safety, accounts).chat(HARMFUL, _user(accounts))
    assistant.chat.assert_not_called()
    assert _user(accounts).strikes == 0


def test_answers_reach_users_without_sources() -> None:
    """Citations and sources are logged, not sent (ADR 029)."""
    assistant = MagicMock()
    assistant.chat.return_value = MagicMock(
        answer="Everton 41% [source: tool predict_match].",
        sources=[MagicMock(source="api.md", excerpt="x", relevance_score=0.8)],
        confidence=0.8,
        model="m",
        retrieved_count=1,
    )
    response = ChatService(assistant).chat(HARMFUL)
    assert (response.answer, response.sources) == ("Everton 41%.", [])
