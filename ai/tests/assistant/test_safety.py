"""Tests for assistant.safety (ADR 027)."""

from __future__ import annotations

import pytest

from assistant.safety import SafetyCheck, SafetyCheckError


class Guard:
    """A guard model that always gives ``reply``."""

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.messages: list[dict[str, str]] = []

    def generate(self, messages: list[dict[str, str]]) -> str:
        self.messages = messages
        return self.reply


def test_safe_question_has_no_categories() -> None:
    guard = Guard("\n\nsafe")
    assert SafetyCheck(guard).harmful_categories("Will Chelsea destroy Everton?") == []
    assert guard.messages == [
        {"role": "user", "content": "Will Chelsea destroy Everton?"}
    ]


def test_unsafe_question_returns_its_hazard_codes() -> None:
    check = SafetyCheck(Guard("\n\nunsafe\nS1, S10"))
    assert check.harmful_categories("...") == ["S1", "S10"]


def test_unsafe_without_codes_still_counts() -> None:
    assert SafetyCheck(Guard("unsafe")).harmful_categories("...") == ["unknown"]


@pytest.mark.parametrize("reply", ["", "I think this is fine", "maybe"])
def test_an_unexpected_reply_fails_closed(reply: str) -> None:
    with pytest.raises(SafetyCheckError):
        SafetyCheck(Guard(reply)).harmful_categories("...")
