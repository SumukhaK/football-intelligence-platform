"""Tests for explainability.explainer."""

from __future__ import annotations

import numpy as np
import pandas as pd

from explainability.explainer import SHAPExplainer
from training.trainer import TrainedModel


def test_shap_explainer_constructs(trained_model: TrainedModel) -> None:
    """SHAPExplainer initialises without error from a TrainedModel."""
    explainer = SHAPExplainer(trained_model)
    assert explainer is not None


def test_shap_values_shape(
    trained_model: TrainedModel, feature_matrix_df: pd.DataFrame
) -> None:
    """shap_values() returns 3D array (n_samples, n_features, n_classes)."""
    explainer = SHAPExplainer(trained_model)
    values = explainer.shap_values(feature_matrix_df)
    n_samples = len(feature_matrix_df)
    n_features = len(trained_model.feature_names)
    n_classes = len(trained_model.classes)
    assert values.shape == (n_samples, n_features, n_classes)


def test_shap_values_are_finite(
    trained_model: TrainedModel, feature_matrix_df: pd.DataFrame
) -> None:
    """SHAP values must contain only finite numbers."""
    explainer = SHAPExplainer(trained_model)
    values = explainer.shap_values(feature_matrix_df)
    assert np.all(np.isfinite(values))


def test_expected_value_shape(trained_model: TrainedModel) -> None:
    """expected_value returns an array with one entry per class."""
    explainer = SHAPExplainer(trained_model)
    base = explainer.expected_value()
    assert base.shape == (len(trained_model.classes),)


def test_expected_value_is_finite(trained_model: TrainedModel) -> None:
    """Base values must be finite numbers."""
    explainer = SHAPExplainer(trained_model)
    base = explainer.expected_value()
    assert np.all(np.isfinite(base))


def test_shap_values_single_row(
    trained_model: TrainedModel, feature_df: pd.DataFrame
) -> None:
    """shap_values() works with a single-row DataFrame."""
    explainer = SHAPExplainer(trained_model)
    values = explainer.shap_values(feature_df)
    assert values.shape == (
        1,
        len(trained_model.feature_names),
        len(trained_model.classes),
    )


def test_imputed_shape(trained_model: TrainedModel, feature_df: pd.DataFrame) -> None:
    """imputed_array() returns shape (n_samples, n_features)."""
    explainer = SHAPExplainer(trained_model)
    imp = explainer.imputed_array(feature_df)
    assert imp.shape == (len(feature_df), len(trained_model.feature_names))
