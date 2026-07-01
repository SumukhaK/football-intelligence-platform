"""Tests for POST /explain."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.app.exceptions import FeatureMissingError


def test_explain_returns_200(
    client: TestClient, valid_features: dict[str, Any]
) -> None:
    """POST /explain returns 200 for a valid request."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": valid_features,
    }
    response = client.post("/explain", json=payload)
    assert response.status_code == 200


def test_explain_response_fields(
    client: TestClient, valid_features: dict[str, Any]
) -> None:
    """POST /explain response includes all required explanation fields."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": valid_features,
    }
    data = client.post("/explain", json=payload).json()
    for field in (
        "predicted_result",
        "probability_home",
        "probability_draw",
        "probability_away",
        "confidence",
        "top_positive_features",
        "top_negative_features",
        "all_contributions",
        "model_version",
        "feature_version",
        "dataset_version",
        "explanation_timestamp",
    ):
        assert field in data, f"Missing field: {field}"


def test_explain_contributions_have_expected_keys(
    client: TestClient, valid_features: dict[str, Any]
) -> None:
    """Each contribution entry has feature_name, feature_value, shap_value."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": valid_features,
    }
    data = client.post("/explain", json=payload).json()
    for entry in data["all_contributions"]:
        assert "feature_name" in entry
        assert "feature_value" in entry
        assert "shap_value" in entry


def test_explain_422_missing_fields(client: TestClient) -> None:
    """POST /explain returns 422 when required fields are absent."""
    response = client.post("/explain", json={"home_team": "Arsenal"})
    assert response.status_code == 422


def test_explain_422_missing_feature_columns(
    client: TestClient,
    mock_explanation_service: MagicMock,
    valid_features: dict[str, Any],
) -> None:
    """POST /explain returns 422 when the service raises FeatureMissingError."""
    mock_explanation_service.explain.side_effect = FeatureMissingError(["home_elo"])
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": valid_features,
    }
    response = client.post("/explain", json=payload)
    assert response.status_code == 422


def test_explain_503_when_service_unavailable(tmp_path: Path) -> None:
    """POST /explain returns 503 when the explanation service is not loaded."""
    from unittest.mock import patch

    from backend.app.config import Settings
    from backend.app.main import create_app

    missing = Settings(
        model_path=tmp_path / "no_model.joblib",
        registry_path=tmp_path / "no_registry.json",
    )
    with patch("backend.app.config._settings", missing):
        with patch("backend.app.main.get_settings", return_value=missing):
            bare_app = create_app()
            with TestClient(bare_app, raise_server_exceptions=False) as c:
                response = c.post(
                    "/explain",
                    json={
                        "home_team": "Arsenal",
                        "away_team": "Chelsea",
                        "features": {"home_elo": 1550.0},
                    },
                )
    assert response.status_code == 503


def test_explain_result_in_valid_outcomes(
    client: TestClient, valid_features: dict[str, Any]
) -> None:
    """POST /explain predicted_result is 'H', 'D', or 'A'."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": valid_features,
    }
    data = client.post("/explain", json=payload).json()
    assert data["predicted_result"] in ("H", "D", "A")
