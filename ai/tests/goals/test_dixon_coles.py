"""Tests for fitting the Dixon-Coles goals model."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import check_grad

from goals.dixon_coles import (
    DixonColesParams,
    GoalsModelConfig,
    _Data,
    _objective,
    fit_dixon_coles,
)

TEAMS = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot"]
ATTACK = np.array([0.45, 0.25, 0.05, -0.05, -0.25, -0.45])
DEFENCE = np.array([0.35, 0.20, 0.00, -0.05, -0.20, -0.30])
HOME_ADVANTAGE = 0.25


def synthetic_league(seasons: int = 6, seed: int = 7) -> pd.DataFrame:
    """Double round robins with known strengths, one fixture per team per week."""
    rng = np.random.default_rng(seed)
    rows = []
    day = pd.Timestamp("2015-08-01")
    for _ in range(seasons * 2):
        for h in range(len(TEAMS)):
            for a in range(len(TEAMS)):
                if h == a:
                    continue
                lam = np.exp(HOME_ADVANTAGE + ATTACK[h] - DEFENCE[a])
                mu = np.exp(ATTACK[a] - DEFENCE[h])
                rows.append(
                    {
                        "match_date": day,
                        "home_team": TEAMS[h],
                        "away_team": TEAMS[a],
                        "full_time_home_goals": rng.poisson(lam),
                        "full_time_away_goals": rng.poisson(mu),
                    }
                )
                day += pd.Timedelta(days=2)
    return pd.DataFrame(rows)


def test_gradient_matches_finite_differences() -> None:
    rng = np.random.default_rng(1)
    n, m = 4, 60
    data = _Data(
        home=rng.integers(0, n, m),
        away=rng.integers(0, n, m),
        x=rng.integers(0, 3, m).astype(float),
        y=rng.integers(0, 3, m).astype(float),
        weight=rng.uniform(0.2, 1.0, m),
        n_teams=n,
    )
    prior = rng.normal(0, 0.1, 2 * n)
    theta = np.concatenate([rng.normal(0, 0.2, 2 * n), [0.1, 0.2, -0.08]])

    def value(t: np.ndarray) -> float:
        return _objective(t, data, prior, 1.5)[0]

    def gradient(t: np.ndarray) -> np.ndarray:
        return _objective(t, data, prior, 1.5)[1]

    assert check_grad(value, gradient, theta) < 1e-4


def test_recovers_known_strengths() -> None:
    matches = synthetic_league(seasons=25)
    config = GoalsModelConfig(xi=0.0, l2=0.1, window_days=10_000)
    params = fit_dixon_coles(matches, pd.Timestamp("2030-01-01"), config)
    attack = np.array([params.attack[t] for t in TEAMS])
    defence = np.array([params.defence[t] for t in TEAMS])
    # Strengths are identified only up to a shared shift, so compare centred.
    assert attack - attack.mean() == pytest.approx(ATTACK - ATTACK.mean(), abs=0.12)
    assert defence - defence.mean() == pytest.approx(DEFENCE - DEFENCE.mean(), abs=0.12)
    assert params.home_advantage == pytest.approx(HOME_ADVANTAGE, abs=0.08)


def test_shrinkage_keeps_the_league_scoring_level() -> None:
    matches = synthetic_league(seasons=2)
    # A high-scoring league: about four goals a game rather than two.
    matches["full_time_home_goals"] += 1
    matches["full_time_away_goals"] += 1
    before = pd.Timestamp(matches["match_date"].max()) + pd.Timedelta(days=1)
    params = fit_dixon_coles(matches, before, GoalsModelConfig(l2=1000.0, xi=0.0))
    lam, mu = params.expected_goals("Charlie", "Delta")
    assert lam + mu == pytest.approx(
        matches[["full_time_home_goals", "full_time_away_goals"]].sum(axis=1).mean(),
        rel=0.05,
    )


def test_only_matches_before_the_cutoff_are_used() -> None:
    matches = synthetic_league(seasons=2)
    cutoff = pd.Timestamp(matches["match_date"].iloc[100])
    params = fit_dixon_coles(matches, cutoff, GoalsModelConfig(window_days=10_000))
    assert params.n_matches == 100
    assert params.fitted_before == str(cutoff.date())


def test_window_drops_old_matches() -> None:
    matches = synthetic_league(seasons=2)
    cutoff = pd.Timestamp(matches["match_date"].iloc[100])
    params = fit_dixon_coles(matches, cutoff, GoalsModelConfig(window_days=20))
    assert params.n_matches == 10


def test_no_matches_raises() -> None:
    with pytest.raises(ValueError, match="No matches"):
        fit_dixon_coles(synthetic_league(seasons=1), pd.Timestamp("2000-01-01"))


def test_time_weighting_follows_recent_form() -> None:
    old = synthetic_league(seasons=2)
    recent = old.copy()
    recent["match_date"] = recent["match_date"] + pd.Timedelta(days=365)
    # In the recent block Foxtrot score freely; decay should let that dominate.
    recent.loc[recent["home_team"] == "Foxtrot", "full_time_home_goals"] += 3
    both = pd.concat([old, recent], ignore_index=True)
    before = pd.Timestamp(both["match_date"].max()) + pd.Timedelta(days=1)
    flat = fit_dixon_coles(both, before, GoalsModelConfig(xi=0.0, window_days=9999))
    decayed = fit_dixon_coles(both, before, GoalsModelConfig(xi=0.01, window_days=9999))
    assert decayed.attack["Foxtrot"] > flat.attack["Foxtrot"]


def test_newcomers_start_near_the_weakest_teams() -> None:
    matches = synthetic_league(seasons=3)
    before = pd.Timestamp(matches["match_date"].max()) + pd.Timedelta(days=1)
    params = fit_dixon_coles(matches, before)
    weakest = sorted(TEAMS, key=lambda t: params.attack[t] + params.defence[t])[:3]
    assert params.newcomer_attack == pytest.approx(
        np.mean([params.attack[t] for t in weakest])
    )
    assert set(weakest) == {"Delta", "Echo", "Foxtrot"}
    lam_new, _ = params.expected_goals("Newcomer", "Charlie")
    lam_top, _ = params.expected_goals("Alpha", "Charlie")
    assert lam_new < lam_top


def test_rho_can_be_fixed_at_zero() -> None:
    matches = synthetic_league(seasons=2)
    before = pd.Timestamp(matches["match_date"].max()) + pd.Timedelta(days=1)
    params = fit_dixon_coles(matches, before, GoalsModelConfig(fit_rho=False))
    assert params.rho == 0.0


def test_round_trips_through_a_dict() -> None:
    matches = synthetic_league(seasons=1)
    before = pd.Timestamp(matches["match_date"].max()) + pd.Timedelta(days=1)
    params = fit_dixon_coles(matches, before, competition="Test League")
    assert DixonColesParams.from_dict(params.to_dict()) == params
