"""Tests for explainability.cache."""

from __future__ import annotations

from pathlib import Path

import pytest

from explainability.cache import ExplainerCache
from explainability.explainer import SHAPExplainer
from training.persistence import save_model
from training.trainer import TrainedModel


def test_cache_starts_empty() -> None:
    """A freshly cleared cache returns nothing."""
    ExplainerCache.clear()
    assert ExplainerCache.size() == 0


def test_get_or_create_returns_explainer(
    trained_model: TrainedModel, tmp_path: Path
) -> None:
    """get_or_create returns a SHAPExplainer instance."""
    ExplainerCache.clear()
    model_path = tmp_path / "model.joblib"
    save_model(trained_model, model_path)
    explainer = ExplainerCache.get_or_create(model_path, version="v1")
    assert isinstance(explainer, SHAPExplainer)


def test_get_or_create_is_idempotent(
    trained_model: TrainedModel, tmp_path: Path
) -> None:
    """Calling get_or_create twice with the same version returns the same object."""
    ExplainerCache.clear()
    model_path = tmp_path / "model.joblib"
    save_model(trained_model, model_path)
    a = ExplainerCache.get_or_create(model_path, version="v1")
    b = ExplainerCache.get_or_create(model_path, version="v1")
    assert a is b


def test_cache_grows_per_version(trained_model: TrainedModel, tmp_path: Path) -> None:
    """Different versions create separate cache entries."""
    ExplainerCache.clear()
    model_path = tmp_path / "model.joblib"
    save_model(trained_model, model_path)
    ExplainerCache.get_or_create(model_path, version="v1")
    ExplainerCache.get_or_create(model_path, version="v2")
    assert ExplainerCache.size() == 2


def test_clear_empties_cache(trained_model: TrainedModel, tmp_path: Path) -> None:
    """clear() removes all cached entries."""
    model_path = tmp_path / "model.joblib"
    save_model(trained_model, model_path)
    ExplainerCache.get_or_create(model_path, version="v1")
    ExplainerCache.clear()
    assert ExplainerCache.size() == 0


def test_missing_model_file_raises(tmp_path: Path) -> None:
    """get_or_create raises an error if the model file does not exist."""
    ExplainerCache.clear()
    with pytest.raises(Exception):  # noqa: B017
        ExplainerCache.get_or_create(tmp_path / "missing.joblib", version="vX")
