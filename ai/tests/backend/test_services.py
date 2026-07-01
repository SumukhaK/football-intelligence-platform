"""Unit tests for backend service layer (no HTTP, no model required)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from backend.app.exceptions import FeatureMissingError
from backend.app.schemas.prediction import PredictionRequest

# ---------------------------------------------------------------------------
# PredictionService unit tests
# ---------------------------------------------------------------------------


def _make_ai_prediction(
    predicted_result: str = "H",
    prob_home: float = 0.55,
    prob_draw: float = 0.25,
    prob_away: float = 0.20,
) -> MagicMock:
    """Return a mock MatchPrediction object."""
    p = MagicMock()
    p.home_team = "Arsenal"
    p.away_team = "Chelsea"
    p.predicted_result = predicted_result
    p.probability_home = prob_home
    p.probability_draw = prob_draw
    p.probability_away = prob_away
    return p


def test_prediction_service_predict_returns_response() -> None:
    """PredictionService.predict() returns a PredictionResponse."""
    from backend.app.services.prediction_service import PredictionService

    mock_predictor = MagicMock()
    mock_predictor.predict.return_value = _make_ai_prediction()
    svc = PredictionService(mock_predictor, model_version="v1")
    request = PredictionRequest(
        home_team="Arsenal",
        away_team="Chelsea",
        features={"home_elo": 1550.0},
    )
    response = svc.predict(request)
    assert response.predicted_result == "H"
    assert response.model_version == "v1"


def test_prediction_service_confidence_is_max_prob() -> None:
    """PredictionService.predict() confidence equals max(probs)."""
    from backend.app.services.prediction_service import PredictionService

    mock_predictor = MagicMock()
    mock_predictor.predict.return_value = _make_ai_prediction(
        prob_home=0.55, prob_draw=0.25, prob_away=0.20
    )
    svc = PredictionService(mock_predictor, model_version="v1")
    response = svc.predict(
        PredictionRequest(
            home_team="Arsenal",
            away_team="Chelsea",
            features={"home_elo": 1550.0},
        )
    )
    assert response.confidence == pytest.approx(0.55)


def test_prediction_service_raises_feature_missing() -> None:
    """PredictionService.predict() raises FeatureMissingError on ValueError."""
    from backend.app.services.prediction_service import PredictionService

    mock_predictor = MagicMock()
    mock_predictor.predict.side_effect = ValueError(
        "Missing feature columns: ['home_elo']"
    )
    svc = PredictionService(mock_predictor, model_version="v1")
    with pytest.raises(FeatureMissingError):
        svc.predict(
            PredictionRequest(
                home_team="Arsenal",
                away_team="Chelsea",
                features={},
            )
        )


# ---------------------------------------------------------------------------
# ExplanationService unit tests
# ---------------------------------------------------------------------------


def _make_ai_explanation() -> MagicMock:
    """Return a mock LocalExplanation object."""

    e = MagicMock()
    e.home_team = "Arsenal"
    e.away_team = "Chelsea"
    e.predicted_result = "H"
    e.probability_home = 0.55
    e.probability_draw = 0.25
    e.probability_away = 0.20
    e.confidence = 0.55
    e.model_version = "v1"
    e.feature_version = "unknown"
    e.dataset_version = "2023-24"
    e.explanation_timestamp = datetime(2026, 6, 30, tzinfo=UTC)

    contrib = MagicMock()
    contrib.feature_name = "home_elo"
    contrib.feature_value = 1550.0
    contrib.shap_value = 0.12

    neg = MagicMock()
    neg.feature_name = "away_elo"
    neg.feature_value = 1480.0
    neg.shap_value = -0.08

    e.top_positive_features = [contrib]
    e.top_negative_features = [neg]
    e.all_contributions = [contrib, neg]
    return e


def test_explanation_service_explain_returns_response() -> None:
    """ExplanationService.explain() returns an ExplanationResponse."""
    from backend.app.services.explanation_service import ExplanationService

    mock_ai = MagicMock()
    mock_ai.explain.return_value = _make_ai_explanation()
    svc = ExplanationService(mock_ai, model_version="v1", dataset_version="2023-24")
    response = svc.explain("Arsenal", "Chelsea", {"home_elo": 1550.0})
    assert response.predicted_result == "H"
    assert len(response.all_contributions) == 2


def test_explanation_service_raises_feature_missing() -> None:
    """ExplanationService.explain() raises FeatureMissingError on ValueError."""
    from backend.app.services.explanation_service import ExplanationService

    mock_ai = MagicMock()
    mock_ai.explain.side_effect = ValueError("Missing feature columns: ['home_elo']")
    svc = ExplanationService(mock_ai, model_version="v1", dataset_version="2023-24")
    with pytest.raises(FeatureMissingError):
        svc.explain("Arsenal", "Chelsea", {})
