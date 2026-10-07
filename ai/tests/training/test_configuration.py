"""Tests for training.configuration."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pytest
from pydantic import ValidationError

from training.configuration import MODEL_FEATURES, TrainingConfig

_ROOT = Path(__file__).resolve().parents[3]
_TOP5_METADATA = _ROOT / "datasets" / "features" / "top5" / "feature_metadata.json"
_LIVE_MODEL = _ROOT / "ai" / "models" / "latest" / "model.joblib"


def test_default_config_is_valid() -> None:
    """Default TrainingConfig constructs without error."""
    config = TrainingConfig()
    assert config.n_estimators == 300
    assert config.learning_rate == 0.1
    assert config.max_depth == 6
    assert config.train_ratio + config.val_ratio < 1.0


def test_config_is_frozen() -> None:
    """TrainingConfig must not be mutated after construction."""
    config = TrainingConfig()
    with pytest.raises(Exception):  # noqa: B017
        config.n_estimators = 999


def test_exclude_columns_contains_post_match_stats() -> None:
    """Exclude columns must include post-match stats; target is excluded separately."""
    config = TrainingConfig()
    assert "full_time_home_goals" in config.exclude_columns
    assert "home_shots" in config.exclude_columns
    assert config.target_column == "result"


def test_exclude_columns_contains_every_odds_column() -> None:
    """Bookmaker odds are benchmarks, never model inputs."""
    config = TrainingConfig()
    for column in [
        "home_odds",
        "draw_odds",
        "away_odds",
        "over_2_5_odds",
        "under_2_5_odds",
    ]:
        assert column in config.exclude_columns


def test_custom_config_overrides() -> None:
    """Custom values are respected."""
    config = TrainingConfig(n_estimators=50, learning_rate=0.05)
    assert config.n_estimators == 50
    assert config.learning_rate == 0.05


def test_invalid_learning_rate_raises() -> None:
    """Learning rate must be positive."""
    with pytest.raises(Exception):  # noqa: B017
        TrainingConfig(learning_rate=-0.1)


def test_train_val_ratios_are_positive() -> None:
    """Train and val ratios must both be between 0 and 1."""
    config = TrainingConfig(train_ratio=0.7, val_ratio=0.15)
    assert 0 < config.train_ratio < 1
    assert 0 < config.val_ratio < 1


def test_default_features_are_the_pinned_42() -> None:
    """The default feature list is the pinned MODEL_FEATURES tuple."""
    config = TrainingConfig()
    assert config.feature_columns == list(MODEL_FEATURES)
    assert len(MODEL_FEATURES) == 42
    assert len(set(MODEL_FEATURES)) == 42


def test_pinned_features_never_include_odds_or_post_match_columns() -> None:
    """No excluded column (odds, goals, match stats, metadata) is a feature."""
    config = TrainingConfig()
    assert not set(MODEL_FEATURES) & set(config.exclude_columns)
    assert config.target_column not in MODEL_FEATURES
    assert not [c for c in MODEL_FEATURES if "odds" in c]


def test_pinned_features_match_the_top5_feature_metadata() -> None:
    """The pinned list equals what the top-5 feature pipeline produces, in order."""
    meta = json.loads(_TOP5_METADATA.read_text(encoding="utf-8"))
    assert list(MODEL_FEATURES) == meta["feature_names"]


@pytest.mark.skipif(not _LIVE_MODEL.exists(), reason="no trained model on disk")
def test_pinned_features_match_the_live_model() -> None:
    """The pinned list is the served model's feature order: no behaviour change."""
    assert list(MODEL_FEATURES) == joblib.load(_LIVE_MODEL).feature_names


def test_excluded_column_as_feature_is_rejected() -> None:
    """Listing an odds column as a feature fails at config time."""
    with pytest.raises(ValidationError, match="home_odds"):
        TrainingConfig(feature_columns=["home_elo_before", "home_odds"])


def test_target_as_feature_is_rejected() -> None:
    """The target column can never be a feature."""
    with pytest.raises(ValidationError, match="result"):
        TrainingConfig(feature_columns=["result"])


def test_duplicate_features_are_rejected() -> None:
    """Each feature appears once."""
    with pytest.raises(ValidationError, match="Duplicate"):
        TrainingConfig(feature_columns=["home_ppg", "home_ppg"])
