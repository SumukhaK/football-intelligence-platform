"""Tests for explainability validation logic."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from explainability.explainer import SHAPExplainer
from training.trainer import TrainedModel


def test_validate_feature_columns_passes(
    trained_model: TrainedModel, feature_df: pd.DataFrame
) -> None:
    """No error when all feature columns are present."""
    explainer = SHAPExplainer(trained_model)
    # Should not raise — simply verify imputed_array returns correct shape.
    imp = explainer.imputed_array(feature_df)
    assert imp.shape == (1, len(trained_model.feature_names))


def test_validate_wrong_columns_raises(trained_model: TrainedModel) -> None:
    """imputed_array raises ValueError when columns don't match feature_names."""
    explainer = SHAPExplainer(trained_model)
    bad_df = pd.DataFrame([{"wrong_col": 1.0, "another": 2.0}])
    with pytest.raises(ValueError, match="Missing feature columns"):
        explainer.imputed_array(bad_df)


def test_shap_values_nan_handling(trained_model: TrainedModel) -> None:
    """shap_values() handles NaN inputs (imputer fills them before SHAP)."""
    explainer = SHAPExplainer(trained_model)
    df_with_nan = pd.DataFrame(
        [{col: float("nan") for col in trained_model.feature_names}]
    )
    values = explainer.shap_values(df_with_nan)
    assert np.all(np.isfinite(values))


def test_shap_values_empty_dataframe_raises(trained_model: TrainedModel) -> None:
    """shap_values() raises an error on an empty DataFrame."""
    explainer = SHAPExplainer(trained_model)
    empty_df = pd.DataFrame(columns=trained_model.feature_names)
    with pytest.raises(Exception):  # noqa: B017
        explainer.shap_values(empty_df)
