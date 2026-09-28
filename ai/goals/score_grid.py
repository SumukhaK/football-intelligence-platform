"""Score grids and everything derived from them: outcomes, markets, top scores.

A score grid is a (max_goals + 1) x (max_goals + 1) array where cell [h, a]
is the probability of the match ending h-a. Every output is a sum over it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import poisson

DEFAULT_MAX_GOALS = 10


def dixon_coles_tau(
    home_goals: np.ndarray, away_goals: np.ndarray, lam: float, mu: float, rho: float
) -> np.ndarray:
    """Dixon-Coles correction factor for each score; 1 outside 0-0, 1-0, 0-1, 1-1."""
    tau = np.ones(np.broadcast(home_goals, away_goals).shape)
    tau = np.where((home_goals == 0) & (away_goals == 0), 1 - lam * mu * rho, tau)
    tau = np.where((home_goals == 0) & (away_goals == 1), 1 + lam * rho, tau)
    tau = np.where((home_goals == 1) & (away_goals == 0), 1 + mu * rho, tau)
    tau = np.where((home_goals == 1) & (away_goals == 1), 1 - rho, tau)
    return tau


def score_grid(
    lam: float, mu: float, rho: float = 0.0, max_goals: int = DEFAULT_MAX_GOALS
) -> np.ndarray:
    """Probability of every score up to ``max_goals`` each, summing to 1."""
    goals = np.arange(max_goals + 1)
    grid = np.outer(poisson.pmf(goals, lam), poisson.pmf(goals, mu))
    grid *= dixon_coles_tau(goals[:, None], goals[None, :], lam, mu, rho)
    grid = np.clip(grid, 0.0, None)
    return np.asarray(grid / grid.sum())


@dataclass(frozen=True)
class ScoreProbability:
    """One scoreline and its probability."""

    home: int
    away: int
    probability: float


@dataclass(frozen=True)
class GoalMarkets:
    """Probabilities of common goal events for one fixture."""

    btts: float
    over_1_5: float
    over_2_5: float
    over_3_5: float
    home_clean_sheet: float
    away_clean_sheet: float


def outcome_probabilities(grid: np.ndarray) -> tuple[float, float, float]:
    """Home win, draw and away win probabilities."""
    home = float(np.tril(grid, -1).sum())
    draw = float(np.trace(grid))
    away = float(np.triu(grid, 1).sum())
    return home, draw, away


def goal_markets(grid: np.ndarray) -> GoalMarkets:
    """Both teams to score, total-goals lines and clean sheets."""
    goals = np.arange(grid.shape[0])
    totals = goals[:, None] + goals[None, :]
    return GoalMarkets(
        btts=float(grid[1:, 1:].sum()),
        over_1_5=float(grid[totals > 1.5].sum()),
        over_2_5=float(grid[totals > 2.5].sum()),
        over_3_5=float(grid[totals > 3.5].sum()),
        home_clean_sheet=float(grid[:, 0].sum()),
        away_clean_sheet=float(grid[0, :].sum()),
    )


def top_scores(grid: np.ndarray, n: int = 5) -> list[ScoreProbability]:
    """The ``n`` most likely scores, most likely first."""
    flat = np.argsort(grid, axis=None)[::-1][:n]
    rows, cols = np.unravel_index(flat, grid.shape)
    return [
        ScoreProbability(home=int(h), away=int(a), probability=float(grid[h, a]))
        for h, a in zip(rows, cols, strict=True)
    ]


def expected_goals(grid: np.ndarray) -> tuple[float, float]:
    """Mean home and away goals under the grid."""
    goals = np.arange(grid.shape[0])
    return float(grid.sum(axis=1) @ goals), float(grid.sum(axis=0) @ goals)
