"""Tests for training.splitter."""

from __future__ import annotations

import pandas as pd
import pytest

from training.configuration import TrainingConfig
from training.splitter import ChronologicalSplitter, DataSplit, get_feature_columns


@pytest.fixture()
def _df() -> pd.DataFrame:
    """Small feature matrix with 30 rows."""
    import numpy as np

    rng = np.random.default_rng(0)
    dates = pd.date_range("2023-08-01", periods=30, freq="7D")
    return pd.DataFrame(
        {
            "match_date": dates,
            "result": rng.choice(["H", "D", "A"], size=30),
            "feat_a": rng.random(30),
            "feat_b": rng.random(30),
            "home_team": "A",
            "away_team": "B",
            "full_time_home_goals": rng.integers(0, 5, 30).astype(float),
        }
    )


def test_get_feature_columns_excludes_non_numeric(_df: pd.DataFrame) -> None:
    """get_feature_columns returns only numeric, non-excluded columns."""
    config = TrainingConfig()
    cols = get_feature_columns(_df, config)
    assert "feat_a" in cols
    assert "feat_b" in cols
    assert "result" not in cols
    assert "home_team" not in cols
    assert "full_time_home_goals" not in cols


def test_chronological_split_sizes(_df: pd.DataFrame) -> None:
    """Split sizes must sum to total rows and respect configured ratios."""
    config = TrainingConfig(train_ratio=0.70, val_ratio=0.15)
    feature_cols = get_feature_columns(_df, config)
    split = ChronologicalSplitter().split(_df, feature_cols, config)

    total = split.train_size + split.val_size + split.test_size
    assert total == len(_df)
    assert split.train_size >= 1
    assert split.val_size >= 1
    assert split.test_size >= 1


def test_split_is_ordered(_df: pd.DataFrame) -> None:
    """Train dates must come before val dates which must come before test dates."""
    config = TrainingConfig()
    feature_cols = get_feature_columns(_df, config)
    split = ChronologicalSplitter().split(_df, feature_cols, config)

    train_max = pd.to_datetime(split.date_range_train[1])
    val_min = pd.to_datetime(split.date_range_val[0])
    val_max = pd.to_datetime(split.date_range_val[1])
    test_min = pd.to_datetime(split.date_range_test[0])

    assert train_max <= val_min
    assert val_max <= test_min


def test_split_shapes_match(_df: pd.DataFrame) -> None:
    """X and y shapes must be consistent within each split."""
    config = TrainingConfig()
    feature_cols = get_feature_columns(_df, config)
    split = ChronologicalSplitter().split(_df, feature_cols, config)

    assert len(split.X_train) == len(split.y_train) == split.train_size
    assert len(split.X_val) == len(split.y_val) == split.val_size
    assert len(split.X_test) == len(split.y_test) == split.test_size


def test_split_no_target_in_features(_df: pd.DataFrame) -> None:
    """Feature matrices must not contain the target column."""
    config = TrainingConfig()
    feature_cols = get_feature_columns(_df, config)
    split = ChronologicalSplitter().split(_df, feature_cols, config)

    assert "result" not in split.X_train.columns
    assert "result" not in split.X_val.columns
    assert "result" not in split.X_test.columns


def test_split_returns_dataclass(_df: pd.DataFrame) -> None:
    """The return type is DataSplit."""
    config = TrainingConfig()
    feature_cols = get_feature_columns(_df, config)
    result = ChronologicalSplitter().split(_df, feature_cols, config)
    assert isinstance(result, DataSplit)
