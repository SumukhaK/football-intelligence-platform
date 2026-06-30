"""Tests for explainability.serializers."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import pytest
from typing import cast

from explainability.serializers import (
    FeatureContribution,
    GlobalSummary,
    LocalExplanation,
    contributions_for_class,
    global_summary_from_shap,
)
from training.trainer import TrainedModel


def _fake_shap_values(
    n_samples: int, n_features: int, n_classes: int, seed: int = 0
) -> np.ndarray:
    """Return reproducible fake SHAP values array."""
    rng = np.random.default_rng(seed)
    return rng.standard_normal((n_samples, n_features, n_classes)).astype(np.float64)


def _fake_feature_values(n_features: int, seed: int = 0) -> list[float]:
    """Return reproducible fake feature values."""
    rng = np.random.default_rng(seed)
    return cast(list[float], rng.random(n_features).tolist())


def test_feature_contribution_constructs() -> None:
    """FeatureContribution must be constructible from basic fields."""
    fc = FeatureContribution(
        feature_name="home_elo",
        feature_value=1550.0,
        shap_value=0.12,
    )
    assert fc.feature_name == "home_elo"
    assert fc.shap_value == pytest.approx(0.12)


def test_feature_contribution_is_frozen() -> None:
    """FeatureContribution must be immutable."""
    fc = FeatureContribution(
        feature_name="home_elo", feature_value=1550.0, shap_value=0.12
    )
    with pytest.raises(Exception):  # noqa: B017
        fc.shap_value = 0.99


def test_contributions_for_class_returns_sorted(
    trained_model: TrainedModel,
) -> None:
    """contributions_for_class returns contributions sorted by |SHAP| descending."""
    n_features = len(trained_model.feature_names)
    shap_vals = _fake_shap_values(1, n_features, len(trained_model.classes))[0, :, 0]
    fv = _fake_feature_values(n_features)
    contribs = contributions_for_class(
        shap_values_for_class=shap_vals,
        feature_values=fv,
        feature_names=trained_model.feature_names,
    )
    magnitudes = [abs(c.shap_value) for c in contribs]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_contributions_for_class_count(trained_model: TrainedModel) -> None:
    """contributions_for_class returns one entry per feature."""
    n_features = len(trained_model.feature_names)
    shap_vals = _fake_shap_values(1, n_features, len(trained_model.classes))[0, :, 0]
    fv = _fake_feature_values(n_features)
    contribs = contributions_for_class(shap_vals, fv, trained_model.feature_names)
    assert len(contribs) == n_features


def test_local_explanation_is_frozen(trained_model: TrainedModel) -> None:
    """LocalExplanation is immutable after construction."""
    n_features = len(trained_model.feature_names)
    shap_vals = _fake_shap_values(1, n_features, 3)[0, :, 0]
    fv = _fake_feature_values(n_features)
    contribs = contributions_for_class(shap_vals, fv, trained_model.feature_names)
    expl = LocalExplanation(
        match_index=0,
        home_team="Arsenal",
        away_team="Chelsea",
        predicted_result="H",
        probability_home=0.5,
        probability_draw=0.3,
        probability_away=0.2,
        confidence=0.5,
        top_positive_features=contribs[:3],
        top_negative_features=[],
        all_contributions=contribs,
        model_version="v1",
        feature_version="v1",
        dataset_version="v1",
        explanation_timestamp=datetime.now(tz=UTC),
    )
    with pytest.raises(Exception):  # noqa: B017
        expl.predicted_result = "A"


def test_local_explanation_serialises(trained_model: TrainedModel) -> None:
    """LocalExplanation.model_dump_json() produces valid JSON."""
    n_features = len(trained_model.feature_names)
    shap_vals = _fake_shap_values(1, n_features, 3)[0, :, 0]
    fv = _fake_feature_values(n_features)
    contribs = contributions_for_class(shap_vals, fv, trained_model.feature_names)
    expl = LocalExplanation(
        match_index=0,
        home_team="Arsenal",
        away_team="Chelsea",
        predicted_result="H",
        probability_home=0.5,
        probability_draw=0.3,
        probability_away=0.2,
        confidence=0.5,
        top_positive_features=contribs[:3],
        top_negative_features=[],
        all_contributions=contribs,
        model_version="v1",
        feature_version="v1",
        dataset_version="v1",
        explanation_timestamp=datetime.now(tz=UTC),
    )
    parsed = json.loads(expl.model_dump_json())
    assert parsed["predicted_result"] == "H"
    assert "all_contributions" in parsed


def test_global_summary_from_shap(trained_model: TrainedModel) -> None:
    """global_summary_from_shap constructs a valid GlobalSummary."""
    n_samples, n_features = 5, len(trained_model.feature_names)
    shap_vals = _fake_shap_values(n_samples, n_features, len(trained_model.classes))
    summary = global_summary_from_shap(
        shap_values=shap_vals,
        feature_names=trained_model.feature_names,
        classes=trained_model.classes,
        model_version="v1",
        feature_version="fv1",
        dataset_version="dv1",
    )
    assert isinstance(summary, GlobalSummary)
    assert summary.n_samples == n_samples
    assert summary.n_features == n_features
    assert len(summary.mean_abs_shap_per_feature) == n_features


def test_global_summary_serialises(trained_model: TrainedModel) -> None:
    """GlobalSummary.model_dump_json() produces valid JSON."""
    n_samples, n_features = 5, len(trained_model.feature_names)
    shap_vals = _fake_shap_values(n_samples, n_features, len(trained_model.classes))
    summary = global_summary_from_shap(
        shap_values=shap_vals,
        feature_names=trained_model.feature_names,
        classes=trained_model.classes,
        model_version="v1",
        feature_version="fv1",
        dataset_version="dv1",
    )
    parsed = json.loads(summary.model_dump_json())
    assert parsed["n_samples"] == n_samples
    assert "mean_abs_shap_per_feature" in parsed
