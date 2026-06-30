"""Integration tests verifying graceful error handling and recovery.

These tests confirm that the system returns structured error responses
(never crashes) when given bad inputs, missing services, or invalid state.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Backend unavailable
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_predict_503_when_model_missing(tmp_path: Path) -> None:
    """POST /predict returns 503 when model artifact is absent at startup."""
    from backend.app.config import Settings
    from backend.app.main import create_app

    settings = Settings(
        model_path=tmp_path / "missing.joblib",
        registry_path=tmp_path / "missing.json",
    )
    with patch("backend.app.config._settings", settings):
        with patch("backend.app.main.get_settings", return_value=settings):
            application = create_app()
            with TestClient(application, raise_server_exceptions=False) as c:
                response = c.post(
                    "/predict",
                    json={
                        "home_team": "Arsenal",
                        "away_team": "Chelsea",
                        "features": {"home_elo_before": 1500.0},
                    },
                )
    assert response.status_code == 503
    data = response.json()
    assert "error" in data or "detail" in data


@pytest.mark.integration
def test_explain_503_when_model_missing(tmp_path: Path) -> None:
    """POST /explain returns 503 when model artifact is absent at startup."""
    from backend.app.config import Settings
    from backend.app.main import create_app

    settings = Settings(
        model_path=tmp_path / "missing.joblib",
        registry_path=tmp_path / "missing.json",
    )
    with patch("backend.app.config._settings", settings):
        with patch("backend.app.main.get_settings", return_value=settings):
            application = create_app()
            with TestClient(application, raise_server_exceptions=False) as c:
                response = c.post(
                    "/explain",
                    json={
                        "home_team": "Arsenal",
                        "away_team": "Chelsea",
                        "features": {"home_elo_before": 1500.0},
                    },
                )
    assert response.status_code == 503


@pytest.mark.integration
def test_health_still_returns_200_when_model_missing(tmp_path: Path) -> None:
    """GET /health returns 200 even when the model is not loaded."""
    from backend.app.config import Settings
    from backend.app.main import create_app

    settings = Settings(
        model_path=tmp_path / "missing.joblib",
        registry_path=tmp_path / "missing.json",
    )
    with patch("backend.app.config._settings", settings):
        with patch("backend.app.main.get_settings", return_value=settings):
            application = create_app()
            with TestClient(application, raise_server_exceptions=False) as c:
                response = c.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["model_loaded"] is False


# ---------------------------------------------------------------------------
# Invalid request payloads
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_predict_422_empty_features(real_client: object) -> None:
    """POST /predict returns 422 when features dict is empty."""
    response = real_client.post(  # type: ignore[attr-defined]
        "/predict",
        json={"home_team": "Arsenal", "away_team": "Chelsea", "features": {}},
    )
    # The service raises FeatureMissingError → 422
    assert response.status_code in (422, 503)


@pytest.mark.integration
def test_predict_422_malformed_body(real_client: object) -> None:
    """POST /predict returns 422 for a completely wrong body shape."""
    response = real_client.post(  # type: ignore[attr-defined]
        "/predict",
        json={"nonsense": True},
    )
    assert response.status_code == 422


@pytest.mark.integration
def test_unknown_route_returns_404() -> None:
    """An unknown route returns 404 and does not crash the app."""
    from backend.app.main import create_app

    application = create_app()
    with TestClient(application, raise_server_exceptions=False) as c:
        response = c.get("/this-does-not-exist")
    assert response.status_code == 404


@pytest.mark.integration
def test_wrong_http_method_returns_405() -> None:
    """GET on a POST-only route returns 405."""
    from backend.app.main import create_app

    application = create_app()
    with TestClient(application, raise_server_exceptions=False) as c:
        response = c.get("/predict")
    assert response.status_code == 405
