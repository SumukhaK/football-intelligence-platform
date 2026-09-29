"""Tests for hyperparameter search by season walk-forward CV (ADR 007)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from training.configuration import TrainingConfig
from training.tuning import parameter_grid, tune

_SEASONS = [f"{2014 + i}/{15 + i}" for i in range(8)]


def _matrix(rows: int = 30) -> pd.DataFrame:
    rng = np.random.default_rng(11)
    frames = []
    for i, season in enumerate(_SEASONS):
        elo_diff = rng.normal(0, 100, rows)
        result = np.where(elo_diff > 40, "H", np.where(elo_diff < -40, "A", "D"))
        frames.append(
            pd.DataFrame(
                {
                    "match_date": pd.date_range(f"{2014 + i}-08-10", periods=rows),
                    "season": season,
                    "competition": "Premier League",
                    "home_team": "A",
                    "away_team": "B",
                    "result": result,
                    "elo_diff": elo_diff,
                    "noise": rng.random(rows),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


@pytest.fixture()
def config() -> TrainingConfig:
    return TrainingConfig(
        cv_folds=2,
        split_strategy="season",
        val_seasons=["2020/21"],
        test_seasons=["2021/22"],
    )


def test_parameter_grid_is_the_full_product() -> None:
    grid = parameter_grid([2, 3], [0.05, 0.1], [50])
    assert len(grid) == 4
    assert {"max_depth": 2, "learning_rate": 0.05, "n_estimators": 50} in grid


def test_tune_ranks_results_by_mean_log_loss(config: TrainingConfig) -> None:
    grid = parameter_grid([1, 4], [0.1], [5, 40])
    results = tune(_matrix(), ["elo_diff", "noise"], config, grid)
    assert len(results) == 4
    losses = [r.mean_log_loss for r in results]
    assert losses == sorted(losses)


def test_tune_only_uses_training_seasons(config: TrainingConfig) -> None:
    grid = parameter_grid([2], [0.1], [10])
    [result] = tune(_matrix(), ["elo_diff", "noise"], config, grid)
    # 6 training seasons of 30 rows; 2 folds validate on the last two.
    assert result.fold_val_sizes == [30, 30]
    assert result.fold_train_sizes == [120, 150]


def test_empty_grid_raises(config: TrainingConfig) -> None:
    with pytest.raises(ValueError, match="grid"):
        tune(_matrix(), ["elo_diff"], config, [])
