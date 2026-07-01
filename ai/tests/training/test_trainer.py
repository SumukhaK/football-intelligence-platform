"""Tests for training.trainer."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from training.configuration import TrainingConfig
from training.splitter import ChronologicalSplitter, get_feature_columns
from training.trainer import ModelTrainer, TrainedModel


@pytest.fixture()
def _trained(
    feature_matrix: pd.DataFrame, training_config: TrainingConfig
) -> TrainedModel:
    """A fully-trained model on the fixture feature matrix."""
    cols = get_feature_columns(feature_matrix, training_config)
    split = ChronologicalSplitter().split(feature_matrix, cols, training_config)
    return ModelTrainer().train(split, training_config)


def test_trained_model_has_three_classes(_trained: TrainedModel) -> None:
    """Model must learn all three result classes."""
    assert set(_trained.classes) == {"H", "D", "A"}


def test_feature_names_match_training_data(
    feature_matrix: pd.DataFrame, training_config: TrainingConfig
) -> None:
    """feature_names must equal the columns used during training."""
    cols = get_feature_columns(feature_matrix, training_config)
    split = ChronologicalSplitter().split(feature_matrix, cols, training_config)
    model = ModelTrainer().train(split, training_config)
    assert model.feature_names == list(split.X_train.columns)


def test_predict_returns_correct_shape(
    feature_matrix: pd.DataFrame, training_config: TrainingConfig
) -> None:
    """predict() returns labels array and probability matrix with correct shapes."""
    cols = get_feature_columns(feature_matrix, training_config)
    split = ChronologicalSplitter().split(feature_matrix, cols, training_config)
    model = ModelTrainer().train(split, training_config)
    labels, probs = ModelTrainer().predict(model, split.X_test)

    n = len(split.X_test)
    assert labels.shape == (n,)
    assert probs.shape == (n, 3)


def test_predict_probabilities_sum_to_one(
    feature_matrix: pd.DataFrame, training_config: TrainingConfig
) -> None:
    """Softmax probabilities must sum to 1 for each row."""
    cols = get_feature_columns(feature_matrix, training_config)
    split = ChronologicalSplitter().split(feature_matrix, cols, training_config)
    model = ModelTrainer().train(split, training_config)
    _, probs = ModelTrainer().predict(model, split.X_test)
    row_sums = probs.sum(axis=1)
    np.testing.assert_allclose(row_sums, np.ones(len(split.X_test)), atol=1e-5)


def test_predict_labels_are_valid_classes(
    feature_matrix: pd.DataFrame, training_config: TrainingConfig
) -> None:
    """All predicted labels must belong to the known class set."""
    cols = get_feature_columns(feature_matrix, training_config)
    split = ChronologicalSplitter().split(feature_matrix, cols, training_config)
    model = ModelTrainer().train(split, training_config)
    labels, _ = ModelTrainer().predict(model, split.X_test)
    assert set(labels).issubset({"H", "D", "A"})


def test_best_iteration_is_non_negative(_trained: TrainedModel) -> None:
    """best_iteration must be a non-negative integer (XGBoost is 0-indexed)."""
    assert _trained.best_iteration >= 0
