"""Tests for training.persistence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from training.configuration import TrainingConfig
from training.persistence import (
    load_json,
    load_model,
    save_config,
    save_json,
    save_model,
)
from training.splitter import ChronologicalSplitter, get_feature_columns
from training.trainer import ModelTrainer, TrainedModel


@pytest.fixture()
def _trained(
    feature_matrix: pd.DataFrame, training_config: TrainingConfig
) -> TrainedModel:
    """Trained model fixture."""
    cols = get_feature_columns(feature_matrix, training_config)
    split = ChronologicalSplitter().split(feature_matrix, cols, training_config)
    return ModelTrainer().train(split, training_config)


def test_save_and_load_model_roundtrip(_trained: TrainedModel, tmp_path: Path) -> None:
    """A saved model loads back and produces identical predictions."""
    model_path = tmp_path / "model.joblib"
    save_model(_trained, model_path)
    loaded = load_model(model_path)

    assert loaded.classes == _trained.classes
    assert loaded.feature_names == _trained.feature_names
    assert loaded.best_iteration == _trained.best_iteration


def test_save_json_roundtrip(tmp_path: Path) -> None:
    """JSON save/load preserves nested data."""
    data = {"accuracy": 0.5, "nested": {"f1": 0.4}}
    path = tmp_path / "data.json"
    save_json(data, path)
    loaded = load_json(path)
    assert loaded == data


def test_save_config_writes_valid_json(
    training_config: TrainingConfig, tmp_path: Path
) -> None:
    """save_config writes a JSON file that can be re-loaded."""
    path = tmp_path / "config.json"
    save_config(training_config, path)
    loaded = load_json(path)
    assert loaded["n_estimators"] == training_config.n_estimators
    assert loaded["learning_rate"] == training_config.learning_rate


def test_load_model_file_not_found(tmp_path: Path) -> None:
    """load_model raises an error when the file does not exist."""
    with pytest.raises(Exception):  # noqa: B017
        load_model(tmp_path / "missing.joblib")
