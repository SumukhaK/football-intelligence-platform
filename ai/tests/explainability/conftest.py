"""Shared fixtures for explainability tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from training.configuration import TrainingConfig
from training.splitter import ChronologicalSplitter, get_feature_columns
from training.trainer import ModelTrainer, TrainedModel


def _make_feature_matrix(n: int = 60, seed: int = 7) -> pd.DataFrame:
    """Return a minimal feature matrix for explainability tests."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-08-01", periods=n, freq="7D")
    return pd.DataFrame(
        {
            "match_date": dates,
            "season": "2023/24",
            "competition": "Premier League",
            "home_team": rng.choice(["Arsenal", "Chelsea", "Liverpool"], size=n),
            "away_team": rng.choice(["Man City", "Tottenham"], size=n),
            "result": rng.choice(["H", "D", "A"], size=n),
            "home_elo": rng.uniform(1400, 1600, n),
            "away_elo": rng.uniform(1400, 1600, n),
            "home_form_wins_last5": rng.random(n),
            "away_form_wins_last5": rng.random(n),
            "home_goals_scored_last5": rng.random(n) * 3,
            "away_goals_scored_last5": rng.random(n) * 3,
            "home_rest_days": rng.integers(3, 14, n).astype(float),
            "away_rest_days": rng.integers(3, 14, n).astype(float),
        }
    )


@pytest.fixture(scope="module")
def trained_model() -> TrainedModel:
    """Trained model for explainability tests (module-scoped to avoid re-training)."""
    df = _make_feature_matrix(n=60)
    config = TrainingConfig(
        n_estimators=20,
        early_stopping_rounds=5,
        cv_folds=3,
    )
    cols = get_feature_columns(df, config)
    split = ChronologicalSplitter().split(df, cols, config)
    return ModelTrainer().train(split, config)


@pytest.fixture(scope="module")
def feature_df(trained_model: TrainedModel) -> pd.DataFrame:
    """Single-row feature DataFrame for testing local explanations."""
    return pd.DataFrame([dict.fromkeys(trained_model.feature_names, 1.0)])


@pytest.fixture(scope="module")
def feature_matrix_df(trained_model: TrainedModel) -> pd.DataFrame:
    """Five-row feature matrix for testing batch operations."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({col: rng.random(5) for col in trained_model.feature_names})
