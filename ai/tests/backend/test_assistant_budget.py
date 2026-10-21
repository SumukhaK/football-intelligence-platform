"""Tests for the assistant's daily token budgets (ADR 036)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from assistant.services.assistant_service import AssistantResponse
from backend.app.schemas.assistant import ChatRequest
from backend.app.services.account_service import AccountService
from backend.app.services.account_store import (
    AccountStore,
    FirestoreAccountStore,
    JsonAccountStore,
    User,
)
from backend.app.services.assistant_budget import AssistantBudget, BudgetExhaustedError
from backend.app.services.chat_service import ChatService
from tests.backend.fake_firestore import FakeFirestore

EMAIL = "sam@example.com"
NOW = datetime(2026, 10, 21, 15, 0, tzinfo=UTC)


class Clock:
    """A clock tests can move forward."""

    def __init__(self) -> None:
        self.now = NOW

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture(params=["json", "firestore"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> AccountStore:
    """Every rule holds for both stores."""
    if request.param == "json":
        return JsonAccountStore(tmp_path / "accounts.json")
    return FirestoreAccountStore(FakeFirestore())


def _budget(store: AccountStore, clock: Clock, total: int = 100_000) -> AssistantBudget:
    return AssistantBudget(
        store, per_user=9_000, total=total, tokens_per_answer=3_000, clock=clock
    )


def test_a_typical_answer_must_still_fit(store: AccountStore) -> None:
    """Two answers fit; after a third the next question is refused."""
    budget = _budget(store, Clock())
    for _ in range(3):
        budget.check(EMAIL)
        budget.charge(EMAIL, 2_500)
    with pytest.raises(BudgetExhaustedError, match="today's questions"):
        budget.check(EMAIL)


def test_budgets_reset_at_midnight_utc(store: AccountStore) -> None:
    clock = Clock()
    budget = _budget(store, clock)
    budget.charge(EMAIL, 9_000)
    with pytest.raises(BudgetExhaustedError):
        budget.check(EMAIL)
    clock.now += timedelta(hours=9)
    budget.check(EMAIL)


def test_the_global_budget_protects_the_bill(store: AccountStore) -> None:
    """Many users together still stop at the total."""
    budget = _budget(store, Clock(), total=6_000)
    budget.charge("a@example.com", 3_000)
    budget.charge("b@example.com", 3_000)
    with pytest.raises(BudgetExhaustedError, match="for today"):
        budget.check("c@example.com")


def test_unreported_tokens_cost_a_typical_answer(store: AccountStore) -> None:
    budget = _budget(store, Clock())
    budget.charge(EMAIL, None)
    allowance = budget.allowance(EMAIL)
    assert allowance is not None
    assert allowance.questions_left == 2
    assert allowance.resets_at == datetime(2026, 10, 22, tzinfo=UTC)


def _chat(
    store: AccountStore, assistant: MagicMock, safety: list[str]
) -> tuple[ChatService, User]:
    accounts = AccountService(store)
    code = accounts.create_invite(EMAIL)
    accounts.redeem_invite(EMAIL, code, "correct horse battery")
    guard = MagicMock()
    guard.harmful_categories.return_value = safety
    user = store.get_user(EMAIL)
    assert user is not None
    return ChatService(assistant, guard, accounts, budget=_budget(store, Clock())), user


def _answer(tokens: int | None, model: str = "gemma") -> AssistantResponse:
    return AssistantResponse("Arsenal win.", [], 0.5, model, 0, tokens_used=tokens)


def test_chat_charges_answers_and_says_what_is_left(store: AccountStore) -> None:
    assistant = MagicMock()
    assistant.chat.return_value = _answer(3_000)
    service, user = _chat(store, assistant, [])
    response = service.chat(ChatRequest(message="Who wins?"), user)
    assert response.questions_left == 2
    service.chat(ChatRequest(message="And next week?"), user)
    service.chat(ChatRequest(message="And after?"), user)
    with pytest.raises(BudgetExhaustedError):
        service.chat(ChatRequest(message="One more?"), user)
    assert assistant.chat.call_count == 3


def test_router_replies_and_refusals_are_free(store: AccountStore) -> None:
    assistant = MagicMock()
    assistant.chat.return_value = _answer(0, model="router")
    service, user = _chat(store, assistant, [])
    for _ in range(5):
        assert (
            service.chat(ChatRequest(message="Player stats?"), user).questions_left == 3
        )
    refusing, user = _chat(store, MagicMock(), ["S1"])
    refusing.chat(ChatRequest(message="How do I hurt the referee?"), user)
    assert store.usage(f"{NOW.date().isoformat()}_{EMAIL}") == 0


def test_a_failed_charge_never_loses_the_answer(store: AccountStore) -> None:
    """The answer is already paid for; a usage write error is only logged."""
    assistant = MagicMock()
    assistant.chat.return_value = _answer(3_000)
    service, user = _chat(store, assistant, [])
    service._budget._store = MagicMock(usage=MagicMock(return_value=0))  # noqa: SLF001
    service._budget._store.add_usage.side_effect = RuntimeError(
        "Firestore down"
    )  # noqa: SLF001
    response = service.chat(ChatRequest(message="Who wins?"), user)
    assert response.answer == "Arsenal win."
    assert response.questions_left is None
