"""Tests for probability scoring, baselines and paired bootstrap comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from evaluation.comparison import (
    bootstrap_interval,
    brier_score,
    class_prior_probabilities,
    implied_probabilities,
    paired_bootstrap_delta,
    ranked_probability_score,
    score_probabilities,
)

_CLASSES = ["A", "D", "H"]


def test_rps_is_zero_for_certain_correct_forecast() -> None:
    probs = np.array([[0.0, 0.0, 1.0]])
    assert ranked_probability_score(["H"], probs, _CLASSES) == pytest.approx(0.0)


def test_rps_penalises_distant_misses_more_than_near_misses() -> None:
    home_sure = np.array([[0.0, 0.0, 1.0]])
    near = ranked_probability_score(["D"], home_sure, _CLASSES)
    far = ranked_probability_score(["A"], home_sure, _CLASSES)
    assert near == pytest.approx(0.5)
    assert far == pytest.approx(1.0)


def test_rps_uses_home_draw_away_order_whatever_the_class_order() -> None:
    probs_adh = np.array([[0.2, 0.3, 0.5]])
    probs_hda = np.array([[0.5, 0.3, 0.2]])
    a = ranked_probability_score(["D"], probs_adh, ["A", "D", "H"])
    b = ranked_probability_score(["D"], probs_hda, ["H", "D", "A"])
    assert a == pytest.approx(b)


def test_brier_score_perfect_and_uniform() -> None:
    assert brier_score(["H"], np.array([[0.0, 0.0, 1.0]]), _CLASSES) == 0.0
    uniform = np.full((1, 3), 1 / 3)
    assert brier_score(["H"], uniform, _CLASSES) == pytest.approx(2 / 3)


def test_score_probabilities_returns_all_metrics() -> None:
    probs = np.array([[0.1, 0.2, 0.7], [0.6, 0.3, 0.1]])
    scores = score_probabilities(["H", "A"], probs, _CLASSES)
    assert set(scores) == {"n", "log_loss", "rps", "brier", "accuracy"}
    assert scores["n"] == 2
    assert scores["accuracy"] == 1.0


def test_implied_probabilities_remove_overround() -> None:
    odds = pd.DataFrame({"home_odds": [2.0], "draw_odds": [3.5], "away_odds": [4.0]})
    probs = implied_probabilities(odds, _CLASSES)
    assert probs.sum(axis=1) == pytest.approx([1.0])
    assert probs[0, 2] > probs[0, 1] > probs[0, 0]


def test_implied_probabilities_rejects_missing_odds() -> None:
    odds = pd.DataFrame({"home_odds": [np.nan], "draw_odds": [3.5], "away_odds": [4.0]})
    with pytest.raises(ValueError, match="missing"):
        implied_probabilities(odds, _CLASSES)


def test_class_prior_probabilities_repeat_training_frequencies() -> None:
    probs = class_prior_probabilities(pd.Series(["H", "H", "D", "A"]), 3, _CLASSES)
    assert probs.shape == (3, 3)
    assert probs[0].tolist() == [0.25, 0.25, 0.5]


def test_paired_bootstrap_delta_detects_a_clearly_better_forecast() -> None:
    rng = np.random.default_rng(0)
    y = rng.choice(["H", "D", "A"], 300)
    confidence = rng.uniform(0.5, 0.9, 300)
    good = np.array(
        [
            [p if c == t else (1 - p) / 2 for c in _CLASSES]
            for t, p in zip(y, confidence, strict=True)
        ]
    )
    uniform = np.full((300, 3), 1 / 3)
    delta = paired_bootstrap_delta(y, good, uniform, _CLASSES, n_resamples=200)
    assert delta.mean < 0
    assert delta.upper < 0
    assert delta.lower <= delta.mean <= delta.upper


def test_paired_bootstrap_delta_is_deterministic() -> None:
    y = ["H", "D", "A", "H"]
    a = np.full((4, 3), 1 / 3)
    b = np.array([[0.2, 0.3, 0.5]] * 4)
    first = paired_bootstrap_delta(y, a, b, _CLASSES, n_resamples=50, seed=7)
    second = paired_bootstrap_delta(y, a, b, _CLASSES, n_resamples=50, seed=7)
    assert first == second


def test_bootstrap_interval_brackets_the_point_estimate() -> None:
    rng = np.random.default_rng(1)
    y = rng.choice(["H", "D", "A"], 200)
    probs = rng.dirichlet([2, 2, 2], 200)
    lower, upper = bootstrap_interval(y, probs, _CLASSES, n_resamples=200)
    point = score_probabilities(y, probs, _CLASSES)["log_loss"]
    assert lower < point < upper


def test_paired_bootstrap_delta_supports_accuracy() -> None:
    y = ["H", "H", "A", "D"]
    right = np.array(
        [[0.1, 0.2, 0.7], [0.1, 0.2, 0.7], [0.7, 0.2, 0.1]] + [[0.1, 0.8, 0.1]]
    )
    wrong = np.array([[0.7, 0.2, 0.1]] * 4)
    delta = paired_bootstrap_delta(
        y, right, wrong, _CLASSES, metric="accuracy", n_resamples=50
    )
    assert delta.lower > 0
