"""Tests for evaluation.cross_validation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from evaluation.cross_validation import CVSummary, run_cross_validation
from training.configuration import TrainingConfig


def _make_data(n: int = 60, seed: int = 0) -> tuple[pd.DataFrame, pd.Series]:
    """Return a small feature matrix and label series."""
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(
        {
            "feat_a": rng.random(n),
            "feat_b": rng.random(n),
        }
    )
    y = pd.Series(rng.choice(["H", "D", "A"], size=n))
    return X, y


def test_cv_returns_summary() -> None:
    """run_cross_validation must return a CVSummary."""
    X, y = _make_data()
    config = TrainingConfig(n_estimators=10, cv_folds=3, early_stopping_rounds=3)
    result = run_cross_validation(X, y, config)
    assert isinstance(result, CVSummary)


def test_cv_fold_count_matches_config() -> None:
    """Number of fold results must equal cv_folds."""
    X, y = _make_data()
    config = TrainingConfig(n_estimators=10, cv_folds=3, early_stopping_rounds=3)
    result = run_cross_validation(X, y, config)
    assert result.n_folds == 3
    assert len(result.fold_results) == 3


def test_cv_mean_accuracy_in_range() -> None:
    """Mean accuracy must be between 0 and 1."""
    X, y = _make_data()
    config = TrainingConfig(n_estimators=10, cv_folds=3, early_stopping_rounds=3)
    result = run_cross_validation(X, y, config)
    assert 0.0 <= result.mean_accuracy <= 1.0


def test_cv_fold_indices_are_sequential() -> None:
    """Fold numbers must be 1-indexed and sequential."""
    X, y = _make_data()
    config = TrainingConfig(n_estimators=10, cv_folds=3, early_stopping_rounds=3)
    result = run_cross_validation(X, y, config)
    folds = [r.fold for r in result.fold_results]
    assert folds == list(range(1, config.cv_folds + 1))


def test_cv_std_is_non_negative() -> None:
    """Standard deviations must be non-negative."""
    X, y = _make_data()
    config = TrainingConfig(n_estimators=10, cv_folds=3, early_stopping_rounds=3)
    result = run_cross_validation(X, y, config)
    assert result.std_accuracy >= 0.0
    assert result.std_f1 >= 0.0
    assert result.std_log_loss >= 0.0
