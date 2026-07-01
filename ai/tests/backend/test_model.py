"""Tests for GET /model."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def test_model_returns_200(client: TestClient) -> None:
    """GET /model returns 200 when a registry entry is available."""
    response = client.get("/model")
    assert response.status_code == 200


def test_model_returns_version(client: TestClient) -> None:
    """GET /model body includes model_version."""
    response = client.get("/model")
    assert response.json()["model_version"] == "test-v1"


def test_model_returns_dataset_version(client: TestClient) -> None:
    """GET /model body includes dataset_version."""
    response = client.get("/model")
    assert response.json()["dataset_version"] == "2023-24"


def test_model_returns_training_timestamp(client: TestClient) -> None:
    """GET /model body includes a training_timestamp string."""
    response = client.get("/model")
    ts = response.json()["training_timestamp"]
    assert isinstance(ts, str)
    assert len(ts) > 0


def test_model_returns_git_commit(client: TestClient) -> None:
    """GET /model body includes the git commit if present."""
    response = client.get("/model")
    assert response.json()["git_commit"] == "abc1234"


def test_model_returns_metrics(client: TestClient) -> None:
    """GET /model body includes evaluation metrics."""
    response = client.get("/model")
    assert "test_accuracy" in response.json()["metrics"]


def test_model_503_when_registry_unavailable(tmp_path: Path) -> None:
    """GET /model returns 503 when the registry is not set."""
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
                response = c.get("/model")
    assert response.status_code == 503


def test_model_503_when_registry_empty(tmp_path: Path) -> None:
    """GET /model returns 503 when registry exists but has no entries."""
    from backend.app.config import Settings
    from backend.app.dependencies import get_explanation_service, get_prediction_service
    from backend.app.main import create_app

    empty_registry = MagicMock()
    empty_registry.latest.return_value = None

    missing = Settings(
        model_path=tmp_path / "no_model.joblib",
        registry_path=tmp_path / "no_registry.json",
    )
    with patch("backend.app.config._settings", missing):
        with patch("backend.app.main.get_settings", return_value=missing):
            bare_app = create_app()
            bare_app.state.registry = empty_registry
            mock_ps = MagicMock()
            mock_es = MagicMock()
            bare_app.dependency_overrides[get_prediction_service] = lambda: mock_ps
            bare_app.dependency_overrides[get_explanation_service] = lambda: mock_es
            with TestClient(bare_app, raise_server_exceptions=False) as c:
                response = c.get("/model")
    assert response.status_code == 503
