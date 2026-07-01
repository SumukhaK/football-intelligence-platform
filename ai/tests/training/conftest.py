"""Shared fixtures for training tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from training.configuration import TrainingConfig


def _make_feature_matrix(n: int = 80, seed: int = 42) -> pd.DataFrame:
    """Return a minimal feature matrix with the same shape as production data."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-08-01", periods=n, freq="7D")
    results = rng.choice(["H", "D", "A"], size=n)
    df = pd.DataFrame(
        {
            "match_date": dates,
            "season": "2023/24",
            "competition": "Premier League",
            "home_team": rng.choice(["Arsenal", "Chelsea", "Liverpool"], size=n),
            "away_team": rng.choice(["Man City", "Tottenham", "Newcastle"], size=n),
            "result": results,
            "home_form_wins_last5": rng.random(n),
            "away_form_wins_last5": rng.random(n),
            "home_elo": rng.uniform(1400, 1600, n),
            "away_elo": rng.uniform(1400, 1600, n),
            "home_goals_scored_last5": rng.random(n) * 3,
            "away_goals_scored_last5": rng.random(n) * 3,
            "home_rest_days": rng.integers(3, 14, n).astype(float),
            "away_rest_days": rng.integers(3, 14, n).astype(float),
        }
    )
    return df


@pytest.fixture()
def feature_matrix() -> pd.DataFrame:
    """Minimal feature matrix for training tests."""
    return _make_feature_matrix(n=80)


@pytest.fixture()
def training_config() -> TrainingConfig:
    """Fast training config for tests (fewer estimators, no early stopping risk)."""
    return TrainingConfig(
        n_estimators=20,
        early_stopping_rounds=5,
        cv_folds=3,
    )
