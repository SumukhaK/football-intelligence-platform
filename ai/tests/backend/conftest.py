"""Shared fixtures for backend tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.schemas.explainability import (
    ExplanationResponse,
    FeatureContributionSchema,
)
from backend.app.schemas.prediction import PredictionResponse
from backend.app.services.explanation_service import ExplanationService
from backend.app.services.prediction_service import PredictionService

# ---------------------------------------------------------------------------
# Stub data helpers
# ---------------------------------------------------------------------------


def make_prediction_response(
    predicted_result: str = "H",
    prob_home: float = 0.55,
    prob_draw: float = 0.25,
    prob_away: float = 0.20,
) -> PredictionResponse:
    """Return a minimal PredictionResponse."""
    return PredictionResponse(
        home_team="Arsenal",
        away_team="Chelsea",
        predicted_result=predicted_result,
        probability_home=prob_home,
        probability_draw=prob_draw,
        probability_away=prob_away,
        confidence=prob_home,
        model_version="test-v1",
    )


def make_explanation_response() -> ExplanationResponse:
    """Return a minimal ExplanationResponse."""
    contrib = FeatureContributionSchema(
        feature_name="home_elo", feature_value=1550.0, shap_value=0.12
    )
    neg_contrib = FeatureContributionSchema(
        feature_name="away_elo", feature_value=1480.0, shap_value=-0.08
    )
    return ExplanationResponse(
        home_team="Arsenal",
        away_team="Chelsea",
        predicted_result="H",
        probability_home=0.55,
        probability_draw=0.25,
        probability_away=0.20,
        confidence=0.55,
        top_positive_features=[contrib],
        top_negative_features=[neg_contrib],
        all_contributions=[contrib, neg_contrib],
        model_version="test-v1",
        feature_version="unknown",
        dataset_version="2023-24",
        explanation_timestamp=datetime(2026, 6, 30, 12, 0, 0, tzinfo=UTC),
    )


# ---------------------------------------------------------------------------
# Mock services
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_prediction_service() -> MagicMock:
    """Return a mock PredictionService."""
    svc = MagicMock(spec=PredictionService)
    svc.predict.return_value = make_prediction_response()
    return svc


@pytest.fixture()
def mock_explanation_service() -> MagicMock:
    """Return a mock ExplanationService."""
    svc = MagicMock(spec=ExplanationService)
    svc.explain.return_value = make_explanation_response()
    return svc


@pytest.fixture()
def mock_registry() -> MagicMock:
    """Return a mock ModelRegistry."""
    from model_registry.registry import (
        ModelEntry,
        ModelRegistry,
    )

    reg = MagicMock(spec=ModelRegistry)
    entry = ModelEntry(
        version="test-v1",
        created_at=datetime(2026, 6, 30, 10, 0, 0, tzinfo=UTC),
        run_dir="/tmp/runs/test",
        source_dataset_version="2023-24",
        feature_matrix_path="/tmp/feature_matrix.parquet",
        git_commit="abc1234",
        framework_versions={"xgboost": "2.0.0"},
        metrics={"test_accuracy": 0.56},
    )
    reg.latest.return_value = entry
    return reg


# ---------------------------------------------------------------------------
# Client fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(
    mock_prediction_service: MagicMock,
    mock_explanation_service: MagicMock,
    mock_registry: MagicMock,
) -> TestClient:
    """TestClient with AI services replaced by mocks."""
    from backend.app.dependencies import get_explanation_service, get_prediction_service

    application = create_app()
    application.dependency_overrides[get_prediction_service] = (
        lambda: mock_prediction_service
    )
    application.dependency_overrides[get_explanation_service] = (
        lambda: mock_explanation_service
    )
    application.state.prediction_service = mock_prediction_service
    application.state.explanation_service = mock_explanation_service
    application.state.registry = mock_registry
    return TestClient(application, raise_server_exceptions=False)


@pytest.fixture()
def valid_features() -> dict[str, Any]:
    """Minimal feature dict accepted by the mock predictor."""
    return {
        "home_elo": 1550.0,
        "away_elo": 1480.0,
        "elo_diff": 70.0,
        "home_form_wins_last5": 0.6,
        "away_form_wins_last5": 0.4,
    }
