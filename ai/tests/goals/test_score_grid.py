"""Tests for score grids and the outputs derived from them."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import poisson

from goals.score_grid import (
    expected_goals,
    goal_markets,
    outcome_probabilities,
    score_grid,
    top_scores,
)


def test_grid_sums_to_one() -> None:
    assert score_grid(1.6, 1.1, rho=-0.1).sum() == pytest.approx(1.0)


def test_zero_rho_is_independent_poisson() -> None:
    grid = score_grid(1.4, 0.9, rho=0.0, max_goals=15)
    goals = np.arange(16)
    expected = np.outer(poisson.pmf(goals, 1.4), poisson.pmf(goals, 0.9))
    assert grid == pytest.approx(expected / expected.sum())


def test_rho_changes_only_the_four_low_scores() -> None:
    plain = score_grid(1.4, 1.2, rho=0.0)
    adjusted = score_grid(1.4, 1.2, rho=-0.12)
    changed = ~np.isclose(plain / plain.sum(), adjusted / adjusted.sum(), rtol=0.02)
    low = np.zeros_like(changed)
    low[:2, :2] = True
    assert not changed[~low].any()
    assert adjusted[0, 0] > plain[0, 0]
    assert adjusted[1, 1] > plain[1, 1]


def test_outcomes_partition_the_grid() -> None:
    grid = score_grid(1.5, 1.0, rho=-0.05)
    home, draw, away = outcome_probabilities(grid)
    assert home + draw + away == pytest.approx(1.0)
    assert draw == pytest.approx(np.trace(grid))
    assert home > away


def test_markets_are_sums_over_the_grid() -> None:
    grid = score_grid(1.3, 1.1)
    markets = goal_markets(grid)
    assert markets.btts == pytest.approx(
        1 - grid[0, :].sum() - grid[:, 0].sum() + grid[0, 0]
    )
    assert markets.over_2_5 == pytest.approx(
        1 - sum(grid[h, a] for h in range(3) for a in range(3) if h + a <= 2)
    )
    assert markets.over_1_5 > markets.over_2_5 > markets.over_3_5
    assert markets.home_clean_sheet == pytest.approx(grid[:, 0].sum())


def test_top_scores_are_sorted_and_distinct() -> None:
    scores = top_scores(score_grid(1.5, 0.8), n=5)
    probabilities = [s.probability for s in scores]
    assert probabilities == sorted(probabilities, reverse=True)
    assert len({(s.home, s.away) for s in scores}) == 5
    assert (scores[0].home, scores[0].away) == (1, 0)


def test_expected_goals_match_the_poisson_means() -> None:
    home, away = expected_goals(score_grid(1.7, 0.8, max_goals=15))
    assert home == pytest.approx(1.7, abs=1e-3)
    assert away == pytest.approx(0.8, abs=1e-3)
