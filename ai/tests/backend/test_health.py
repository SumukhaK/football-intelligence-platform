"""Tests for GET /health."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """GET /health returns 200 with status='ok'."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_model_loaded_true(client: TestClient) -> None:
    """GET /health reports model_loaded=True when mock services are wired."""
    response = client.get("/health")
    assert response.json()["model_loaded"] is True


def test_health_explainability_available_true(client: TestClient) -> None:
    """GET /health reports explainability_available=True when mock services are set."""
    response = client.get("/health")
    assert response.json()["explainability_available"] is True


def test_health_includes_version(client: TestClient) -> None:
    """GET /health includes a non-empty version string."""
    response = client.get("/health")
    assert response.json()["version"] != ""


def test_health_no_model_loaded(tmp_path: Path) -> None:
    """GET /health reports model_loaded=False when model path is missing."""
    from backend.app.config import Settings
    from backend.app.main import create_app

    missing_settings = Settings(
        model_path=tmp_path / "no_model.joblib",
        registry_path=tmp_path / "no_registry.json",
    )
    with patch("backend.app.config._settings", missing_settings):
        with patch("backend.app.main.get_settings", return_value=missing_settings):
            bare_app = create_app()
            with TestClient(bare_app, raise_server_exceptions=False) as c:
                response = c.get("/health")
    assert response.status_code == 200
    assert response.json()["model_loaded"] is False
    assert response.json()["explainability_available"] is False
