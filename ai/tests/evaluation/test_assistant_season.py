"""Tests for evaluation.assistant_season."""

from __future__ import annotations

from datetime import date

from evaluation.assistant_season import mentions, score_answer

TODAY = date(2026, 10, 8)
OUTPUT = {"leaders": {"most_likely_first": {"team": "Man City", "chance_first": 0.621}}}


def test_mentions_accepts_full_club_names() -> None:
    """ "Manchester City" counts as naming Man City."""
    assert mentions("Manchester City should top the table.", "Man City")
    assert not mentions("Arsenal should top the table.", "Man City")


def test_answer_quoting_the_tool_passes() -> None:
    """Naming the expected team with the tool's numbers passes."""
    result = score_answer(
        "Who tops it?", "Man City, 62.1% likely.", "Man City", OUTPUT, TODAY
    )
    assert result.passed


def test_invented_number_fails() -> None:
    """A number the tool never returned fails the case."""
    result = score_answer(
        "Who tops it?", "Man City with 40 points.", "Man City", OUTPUT, TODAY
    )
    assert result.ungrounded == ["40"]
    assert not result.passed


def test_refusal_may_name_the_current_and_next_season() -> None:
    """The router's next-season reply names both seasons; that is not invented."""
    answer = "I can only answer about 2026/27 and earlier ones; 2027/28 hasn't started."
    assert score_answer("Next season?", answer, None, None, TODAY).passed
