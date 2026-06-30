"""Tests for explainability.services.explanation_service."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from explainability.serializers import LocalExplanation
from explainability.services.explanation_service import ExplanationService
from training.persistence import save_model
from training.trainer import TrainedModel


@pytest.fixture()
def _service(trained_model: TrainedModel, tmp_path: Path) -> ExplanationService:
    """ExplanationService backed by a saved model file."""
    model_path = tmp_path / "model.joblib"
    save_model(trained_model, model_path)
    return ExplanationService(model_path)


def test_service_explain_returns_local_explanation(
    _service: ExplanationService,
    feature_df: pd.DataFrame,
) -> None:
    """explain() returns a LocalExplanation."""
    result = _service.explain(feature_df, "Arsenal", "Chelsea")
    assert isinstance(result, LocalExplanation)


def test_service_teams_preserved(
    _service: ExplanationService,
    feature_df: pd.DataFrame,
) -> None:
    """explain() passes home_team and away_team through unchanged."""
    result = _service.explain(feature_df, "Arsenal", "Chelsea")
    assert result.home_team == "Arsenal"
    assert result.away_team == "Chelsea"


def test_service_predicted_result_is_valid(
    _service: ExplanationService,
    feature_df: pd.DataFrame,
) -> None:
    """predicted_result must be one of the known outcome classes."""
    result = _service.explain(feature_df, "Arsenal", "Chelsea")
    assert result.predicted_result in {"H", "D", "A"}


def test_service_probabilities_sum_to_one(
    _service: ExplanationService,
    feature_df: pd.DataFrame,
) -> None:
    """Home + draw + away probabilities must sum to 1."""
    result = _service.explain(feature_df, "Arsenal", "Chelsea")
    total = result.probability_home + result.probability_draw + result.probability_away
    assert abs(total - 1.0) < 1e-5


def test_service_contributions_count(
    _service: ExplanationService,
    feature_df: pd.DataFrame,
    trained_model: TrainedModel,
) -> None:
    """all_contributions length must equal the number of model features."""
    result = _service.explain(feature_df, "Arsenal", "Chelsea")
    assert len(result.all_contributions) == len(trained_model.feature_names)


def test_service_confidence_is_max_prob(
    _service: ExplanationService,
    feature_df: pd.DataFrame,
) -> None:
    """confidence must equal max(probability_home, probability_draw, probability_away)."""
    result = _service.explain(feature_df, "Arsenal", "Chelsea")
    expected = max(
        result.probability_home, result.probability_draw, result.probability_away
    )
    assert result.confidence == pytest.approx(expected)


def test_service_missing_column_raises(
    _service: ExplanationService,
) -> None:
    """explain() raises ValueError when required feature columns are missing."""
    bad_df = pd.DataFrame([{"wrong_col": 1.0}])
    with pytest.raises(ValueError, match="Missing feature columns"):
        _service.explain(bad_df, "Arsenal", "Chelsea")


def test_service_top_positive_features_are_positive(
    _service: ExplanationService,
    feature_df: pd.DataFrame,
) -> None:
    """All entries in top_positive_features must have SHAP value >= 0."""
    result = _service.explain(feature_df, "Arsenal", "Chelsea")
    for fc in result.top_positive_features:
        assert fc.shap_value >= 0.0


def test_service_top_negative_features_are_negative(
    _service: ExplanationService,
    feature_df: pd.DataFrame,
) -> None:
    """All entries in top_negative_features must have SHAP value <= 0."""
    result = _service.explain(feature_df, "Arsenal", "Chelsea")
    for fc in result.top_negative_features:
        assert fc.shap_value <= 0.0
