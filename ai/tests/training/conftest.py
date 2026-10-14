"""Shared fixtures for training tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from training.configuration import TrainingConfig
from training.pipeline import TrainingPipeline

FEATURES = [
    "home_form_wins_last5",
    "away_form_wins_last5",
    "home_elo",
    "away_elo",
    "home_goals_scored_last5",
    "away_goals_scored_last5",
    "home_rest_days",
    "away_rest_days",
]


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
        feature_columns=FEATURES,
        n_estimators=20,
        early_stopping_rounds=5,
        cv_folds=3,
    )


REFIT_SEASONS = ["2019/20", "2020/21", "2021/22", "2022/23", "2023/24", "2024/25"]
REFIT_FEATURES = ["home_elo_before", "away_elo_before"]
_REFIT_MATRIX = "features/feature_matrix.parquet"


def _write_refit_matrix(cwd: Path) -> str:
    """Write a six-season matrix under ``cwd``; return its relative path."""
    rng = np.random.default_rng(3)
    frames = [
        pd.DataFrame(
            {
                "match_date": pd.date_range(f"{2019 + i}-08-10", periods=40),
                "season": season,
                "competition": "Premier League",
                "home_team": "A",
                "away_team": "B",
                "result": rng.choice(["H", "D", "A"], 40),
                "home_elo_before": rng.uniform(1300, 1700, 40),
                "away_elo_before": rng.uniform(1300, 1700, 40),
            }
        )
        for i, season in enumerate(REFIT_SEASONS)
    ]
    path = cwd / _REFIT_MATRIX
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(frames, ignore_index=True).to_parquet(path)
    return _REFIT_MATRIX


@pytest.fixture()
def refit_matrix(tmp_path: Path) -> pd.DataFrame:
    """The six-season matrix used by the refit tests."""
    return pd.read_parquet(tmp_path / _write_refit_matrix(tmp_path))


@pytest.fixture()
def source_run(tmp_path: Path) -> Path:
    """A season-split run that was not promoted, as the refit's source."""
    config = TrainingConfig(
        feature_columns=REFIT_FEATURES,
        n_estimators=30,
        early_stopping_rounds=3,
        cv_folds=2,
        split_strategy="season",
        val_seasons=["2021/22"],
        test_seasons=["2022/23"],
        holdout_seasons=["2023/24"],
        feature_matrix_path=_write_refit_matrix(tmp_path),
    )
    return Path(TrainingPipeline(config).run(tmp_path, promote=False)["run_dir"])
