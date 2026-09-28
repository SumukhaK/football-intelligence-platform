"""Tests for goals-model metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from evaluation.goals_metrics import (
    binary_scores,
    bookmaker_over_2_5,
    bootstrap_mean_difference,
    market_comparison,
    outcome_metrics,
    reliability,
    scoreline_metrics,
)


def forecasts() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "home_goals": [2, 0, 1, 3],
            "away_goals": [1, 0, 1, 2],
            "result": ["H", "D", "D", "H"],
            "p_score": [0.10, 0.08, 0.12, 0.02],
            "top1_hit": [False, False, True, False],
            "top3_hit": [True, False, True, False],
            "p_H": [0.5, 0.3, 0.35, 0.6],
            "p_D": [0.25, 0.4, 0.3, 0.2],
            "p_A": [0.25, 0.3, 0.35, 0.2],
            "p_over_2_5": [0.55, 0.35, 0.45, 0.6],
            "p_btts": [0.5, 0.4, 0.5, 0.55],
            "over_2_5_odds": [1.8, 2.4, np.nan, 1.6],
            "under_2_5_odds": [2.0, 1.55, np.nan, 2.3],
        }
    )


def test_scoreline_metrics() -> None:
    m = scoreline_metrics(forecasts())
    expected = -np.mean(np.log([0.10, 0.08, 0.12, 0.02]))
    assert m["scoreline_log_loss"] == pytest.approx(expected)
    assert m["top1_hit_rate"] == 0.25
    assert m["top3_hit_rate"] == 0.5


def test_binary_scores_perfect_and_uninformed() -> None:
    happened = pd.Series([True, False])
    assert binary_scores(pd.Series([1.0, 0.0]), happened)["brier"] == pytest.approx(0)
    assert binary_scores(pd.Series([0.5, 0.5]), happened)["brier"] == 0.25


def test_bookmaker_margin_is_removed() -> None:
    p = bookmaker_over_2_5(forecasts().dropna())
    assert p.iloc[0] == pytest.approx((1 / 1.8) / (1 / 1.8 + 1 / 2.0))


def test_market_comparison_uses_only_priced_matches() -> None:
    m = market_comparison(forecasts())
    assert m["over_2_5_with_odds"]["matches"] == 3
    assert set(m) == {"btts", "over_2_5", "over_2_5_with_odds"}


def test_reliability_counts_every_match() -> None:
    f = forecasts()
    bins = reliability(f["p_over_2_5"], f["home_goals"] + f["away_goals"] > 2)
    assert sum(b["matches"] for b in bins) == 4


def test_outcome_metrics_score_the_implied_probabilities() -> None:
    m = outcome_metrics(forecasts())
    assert m["n"] == 4
    assert 0 < m["log_loss"] < 2


def test_bootstrap_difference_of_identical_forecasts_is_zero() -> None:
    a = np.array([0.1, 0.4, 0.2])
    d = bootstrap_mean_difference(a, a, n_resamples=50)
    assert d == {"mean": 0.0, "lower": 0.0, "upper": 0.0}
