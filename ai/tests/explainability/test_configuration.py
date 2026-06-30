"""Tests for explainability.configuration."""

from __future__ import annotations

import pytest

from explainability.configuration import ExplainabilityConfig


def test_default_config_constructs() -> None:
    """Default ExplainabilityConfig builds without error."""
    config = ExplainabilityConfig()
    assert config.n_top_features > 0
    assert config.n_local_samples > 0
    assert config.n_dependence_plots > 0


def test_config_is_frozen() -> None:
    """ExplainabilityConfig is immutable after construction."""
    config = ExplainabilityConfig()
    with pytest.raises(Exception):  # noqa: B017
        config.n_top_features = 99


def test_default_paths_are_set() -> None:
    """Default model and feature matrix paths are non-empty strings."""
    config = ExplainabilityConfig()
    assert config.model_path
    assert config.feature_matrix_path
    assert config.explanations_dir


def test_custom_overrides_accepted() -> None:
    """Custom values are stored correctly."""
    config = ExplainabilityConfig(n_top_features=5, n_local_samples=3)
    assert config.n_top_features == 5
    assert config.n_local_samples == 3


def test_invalid_n_top_features_raises() -> None:
    """n_top_features must be positive."""
    with pytest.raises(Exception):  # noqa: B017
        ExplainabilityConfig(n_top_features=0)


def test_invalid_n_local_samples_raises() -> None:
    """n_local_samples must be positive."""
    with pytest.raises(Exception):  # noqa: B017
        ExplainabilityConfig(n_local_samples=-1)
