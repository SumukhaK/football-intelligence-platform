"""Tests for POST /predict."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.app.exceptions import FeatureMissingError


def test_predict_returns_200(
    client: TestClient, valid_features: dict[str, Any]
) -> None:
    """POST /predict returns 200 for a valid request."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": valid_features,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200


def test_predict_response_fields(
    client: TestClient, valid_features: dict[str, Any]
) -> None:
    """POST /predict response includes all required fields."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": valid_features,
    }
    data = client.post("/predict", json=payload).json()
    assert "predicted_result" in data
    assert "probability_home" in data
    assert "probability_draw" in data
    assert "probability_away" in data
    assert "confidence" in data
    assert "model_version" in data


def test_predict_result_is_valid_outcome(
    client: TestClient, valid_features: dict[str, Any]
) -> None:
    """POST /predict predicted_result is 'H', 'D', or 'A'."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": valid_features,
    }
    data = client.post("/predict", json=payload).json()
    assert data["predicted_result"] in ("H", "D", "A")


def test_predict_probabilities_between_0_and_1(
    client: TestClient, valid_features: dict[str, Any]
) -> None:
    """POST /predict probabilities are in [0, 1]."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": valid_features,
    }
    data = client.post("/predict", json=payload).json()
    for key in (
        "probability_home",
        "probability_draw",
        "probability_away",
        "confidence",
    ):
        assert 0.0 <= data[key] <= 1.0, f"{key} out of range: {data[key]}"


def test_predict_422_missing_home_team(
    client: TestClient, valid_features: dict[str, Any]
) -> None:
    """POST /predict returns 422 when home_team is absent."""
    response = client.post(
        "/predict", json={"away_team": "Chelsea", "features": valid_features}
    )
    assert response.status_code == 422


def test_predict_422_missing_features(client: TestClient) -> None:
    """POST /predict returns 422 when features dict is absent."""
    response = client.post(
        "/predict", json={"home_team": "Arsenal", "away_team": "Chelsea"}
    )
    assert response.status_code == 422


def test_predict_422_empty_home_team(
    client: TestClient, valid_features: dict[str, Any]
) -> None:
    """POST /predict returns 422 when home_team is an empty string."""
    payload = {"home_team": "", "away_team": "Chelsea", "features": valid_features}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_422_missing_feature_columns(
    client: TestClient,
    mock_prediction_service: MagicMock,
    valid_features: dict[str, Any],
) -> None:
    """POST /predict returns 422 when the service raises FeatureMissingError."""
    mock_prediction_service.predict.side_effect = FeatureMissingError(["home_elo"])
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": valid_features,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert "missing" in response.json()


def test_predict_503_when_service_unavailable(tmp_path: Path) -> None:
    """POST /predict returns 503 when the prediction service is not loaded."""
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
                    "/predict",
                    json={
                        "home_team": "Arsenal",
                        "away_team": "Chelsea",
                        "features": {"home_elo": 1550.0},
                    },
                )
    assert response.status_code == 503
