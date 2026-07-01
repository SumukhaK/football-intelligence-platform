"""Tests for training.configuration."""

from __future__ import annotations

import pytest

from training.configuration import TrainingConfig


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
