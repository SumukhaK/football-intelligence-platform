"""Tests for evaluation.assistant_abstention."""

from __future__ import annotations

from unittest.mock import MagicMock

from evaluation.assistant_abstention import (
    ANSWERABLE,
    REFUSAL,
    UNANSWERABLE,
    CaseResult,
    is_refusal,
    run_cases,
)


def test_is_refusal_matches_the_prompt_phrase() -> None:
    """The exact phrase counts, with or without trailing explanation."""
    assert is_refusal(REFUSAL)
    assert is_refusal(REFUSAL + " The context covers model metrics only.")
    assert not is_refusal("Arsenal's manager is not in my sources, but ...")


def test_case_passes_only_when_refusal_matches_expectation() -> None:
    """Refusing an answerable question fails, as does answering an unanswerable one."""
    assert CaseResult("q", REFUSAL, should_refuse=True).passed
    assert not CaseResult("q", REFUSAL, should_refuse=False).passed
    assert CaseResult("q", "XGBoost handles NaNs.", should_refuse=False).passed
    assert not CaseResult("q", "Bobby Moore lifted it.", should_refuse=True).passed


def test_run_cases_asks_every_question() -> None:
    """Every question goes to the chat endpoint with the right expectation."""
    client = MagicMock()
    client.post.return_value.json.return_value = {"answer": REFUSAL}

    results = run_cases(client)

    assert len(results) == len(ANSWERABLE) + len(UNANSWERABLE)
    assert [r.should_refuse for r in results].count(True) == len(UNANSWERABLE)
    client.post.assert_any_call("/v2/assistant/chat", json={"message": ANSWERABLE[0]})
