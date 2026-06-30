"""Tests for explainability.plots.shap_plots."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from explainability.explainer import SHAPExplainer
from explainability.plots.shap_plots import (
    save_dependence_plot,
    save_feature_importance_plot,
    save_force_plot,
    save_summary_plot,
    save_waterfall_plot,
)
from training.trainer import TrainedModel


@pytest.fixture()
def _explainer(trained_model: TrainedModel) -> SHAPExplainer:
    """SHAPExplainer for plot tests."""
    return SHAPExplainer(trained_model)


def test_save_summary_plot_creates_file(
    _explainer: SHAPExplainer,
    trained_model: TrainedModel,
    feature_matrix_df: pd.DataFrame,
    tmp_path: Path,
) -> None:
    """save_summary_plot writes a PNG file."""
    out = tmp_path / "summary.png"
    shap_values = _explainer.shap_values(feature_matrix_df)
    imp = _explainer.imputed_array(feature_matrix_df)
    save_summary_plot(shap_values, imp, trained_model.feature_names, out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_save_feature_importance_plot_creates_file(
    _explainer: SHAPExplainer,
    trained_model: TrainedModel,
    feature_matrix_df: pd.DataFrame,
    tmp_path: Path,
) -> None:
    """save_feature_importance_plot writes a PNG file."""
    out = tmp_path / "importance.png"
    shap_values = _explainer.shap_values(feature_matrix_df)
    save_feature_importance_plot(shap_values, trained_model.feature_names, out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_save_waterfall_plot_creates_file(
    _explainer: SHAPExplainer,
    trained_model: TrainedModel,
    feature_df: pd.DataFrame,
    tmp_path: Path,
) -> None:
    """save_waterfall_plot writes a PNG file for a single sample."""
    out = tmp_path / "waterfall.png"
    shap_values = _explainer.shap_values(feature_df)
    base_values = _explainer.expected_value()
    imp = _explainer.imputed_array(feature_df)
    # Use the SHAP values for class index 0
    class_idx = 0
    save_waterfall_plot(
        shap_values_row=shap_values[0, :, class_idx],
        base_value=float(base_values[class_idx]),
        feature_values=imp[0].tolist(),
        feature_names=trained_model.feature_names,
        output_path=out,
    )
    assert out.exists()
    assert out.stat().st_size > 0


def test_save_force_plot_creates_file(
    _explainer: SHAPExplainer,
    trained_model: TrainedModel,
    feature_df: pd.DataFrame,
    tmp_path: Path,
) -> None:
    """save_force_plot writes a PNG file for a single sample."""
    out = tmp_path / "force.png"
    shap_values = _explainer.shap_values(feature_df)
    base_values = _explainer.expected_value()
    imp = _explainer.imputed_array(feature_df)
    class_idx = 0
    save_force_plot(
        shap_values_row=shap_values[0, :, class_idx],
        base_value=float(base_values[class_idx]),
        feature_values=imp[0].tolist(),
        feature_names=trained_model.feature_names,
        output_path=out,
    )
    assert out.exists()
    assert out.stat().st_size > 0


def test_save_dependence_plot_creates_file(
    _explainer: SHAPExplainer,
    trained_model: TrainedModel,
    feature_matrix_df: pd.DataFrame,
    tmp_path: Path,
) -> None:
    """save_dependence_plot writes a PNG file for a single feature."""
    out = tmp_path / "dependence.png"
    shap_values = _explainer.shap_values(feature_matrix_df)
    imp = _explainer.imputed_array(feature_matrix_df)
    feature_name = trained_model.feature_names[0]
    save_dependence_plot(
        feature_name=feature_name,
        shap_values=shap_values,
        feature_values_matrix=imp,
        feature_names=trained_model.feature_names,
        output_path=out,
    )
    assert out.exists()
    assert out.stat().st_size > 0
