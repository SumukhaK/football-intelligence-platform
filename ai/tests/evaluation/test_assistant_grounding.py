"""Tests for evaluation.assistant_grounding."""

from __future__ import annotations

import pytest

from evaluation.assistant_grounding import (
    matches,
    quotes_prediction,
    score_prediction_answer,
    score_unknown_team_answer,
    ungrounded_numbers,
)

PREDICTION = {
    "predicted_result": "H",
    "probability_home": 0.4712,
    "probability_draw": 0.2861,
    "probability_away": 0.2427,
    "confidence": 0.4712,
    "model_version": "v20261001",
}
QUESTION = "What does the model predict for Arsenal vs Leeds in the Premier League?"


@pytest.mark.parametrize("token", ["47", "47.1", "47.12", "0.47", "0.471", "0.4712"])
def test_matches_accepts_roundings_of_a_probability(token: str) -> None:
    """A probability may be quoted as a decimal or a percentage, rounded."""
    assert matches(token, 0.4712)


@pytest.mark.parametrize("token", ["0", "1", "48", "47.3", "0.5", "52"])
def test_matches_rejects_other_numbers(token: str) -> None:
    """Bare integers and wrongly rounded values do not count as quotes."""
    assert not matches(token, 0.4712)


def test_grounded_answer_passes() -> None:
    """Quoting the API's probabilities, as percentages, passes."""
    answer = (
        "The model predicts a home win: 47.1% home, 28.6% draw, 24.3% away "
        "[source: tool predict_match]."
    )
    result = score_prediction_answer(QUESTION, answer, [PREDICTION])
    assert result.passed


def test_invented_number_fails() -> None:
    """A number the API never returned is flagged."""
    answer = "Arsenal are 47% favourites and have won 8 of their last 10."
    result = score_prediction_answer(QUESTION, answer, [PREDICTION])
    assert result.ungrounded == ["8", "10"]
    assert not result.passed


def test_answer_without_the_prediction_fails() -> None:
    """An answer that dodges the probability does not count as quoting it."""
    result = score_prediction_answer(QUESTION, "Arsenal should win.", [PREDICTION])
    assert not result.quoted_prediction
    assert not result.passed


def test_numbers_from_the_question_are_allowed() -> None:
    """Numbers the user wrote, such as in a team name, are not invented."""
    assert ungrounded_numbers("Schalke 04 at 47%.", ["Schalke 04", "0.4712"]) == []


def test_quotes_prediction_uses_the_predicted_outcome() -> None:
    """Only the predicted outcome's probability counts as the quote."""
    assert not quotes_prediction("A draw is 28.6% likely.", PREDICTION)


def test_unknown_team_answer_must_not_invent_numbers() -> None:
    """For a team the API rejects, any probability in the answer is invented."""
    question = "What does the model predict for Atlantis FC vs Arsenal?"
    honest = "Atlantis FC is not in the Premier League, so I can't predict it."
    assert score_unknown_team_answer(question, honest).passed
    assert not score_unknown_team_answer(question, "Arsenal 65% to win.").passed
