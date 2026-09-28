"""Tests for walk-forward cross-validation by season (ADR 007)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from evaluation.cross_validation import run_season_cross_validation
from training.configuration import TrainingConfig

_SEASONS = [f"{2015 + i}/{16 + i}" for i in range(6)]


def _data(rows: int = 30) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    rng = np.random.default_rng(3)
    n = rows * len(_SEASONS)
    X = pd.DataFrame({"feat_a": rng.random(n), "feat_b": rng.random(n)})
    y = pd.Series(rng.choice(["H", "D", "A"], n))
    seasons = pd.Series(np.repeat(_SEASONS, rows))
    return X, y, seasons


@pytest.fixture()
def config() -> TrainingConfig:
    return TrainingConfig(n_estimators=10, cv_folds=3)


def test_each_fold_validates_on_one_later_season(config: TrainingConfig) -> None:
    X, y, seasons = _data()
    summary = run_season_cross_validation(X, y, seasons, config)
    assert summary.n_folds == 3
    assert [r.val_size for r in summary.fold_results] == [30, 30, 30]
    assert [r.train_size for r in summary.fold_results] == [90, 120, 150]


def test_metrics_are_finite(config: TrainingConfig) -> None:
    X, y, seasons = _data()
    summary = run_season_cross_validation(X, y, seasons, config)
    assert np.isfinite(summary.mean_log_loss)
    assert 0.0 <= summary.mean_accuracy <= 1.0


def test_too_few_seasons_raises(config: TrainingConfig) -> None:
    X, y, seasons = _data()
    keep = seasons.isin(_SEASONS[:3])
    with pytest.raises(ValueError, match="seasons"):
        run_season_cross_validation(X[keep], y[keep], seasons[keep], config)
