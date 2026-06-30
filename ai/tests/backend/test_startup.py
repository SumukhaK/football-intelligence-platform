"""Tests for application startup and dependency injection."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


def test_create_app_returns_fastapi_app() -> None:
    """create_app() returns a FastAPI instance."""
    from fastapi import FastAPI

    from backend.app.main import create_app

    application = create_app()
    assert isinstance(application, FastAPI)


def test_lifespan_sets_state_to_none_when_model_missing(tmp_path: Path) -> None:
    """Lifespan sets prediction_service=None when model_path does not exist."""
    from backend.app.config import Settings
    from backend.app.main import create_app

    missing = Settings(
        model_path=tmp_path / "no_model.joblib",
        registry_path=tmp_path / "no_registry.json",
    )
    with patch("backend.app.config._settings", missing):
        with patch("backend.app.main.get_settings", return_value=missing):
            application = create_app()
            with TestClient(application, raise_server_exceptions=True):
                assert application.state.prediction_service is None


def test_app_has_all_routes() -> None:
    """create_app() registers /health, /model, /predict, /explain."""
    from backend.app.main import create_app

    application = create_app()
    schema = application.openapi()
    paths = set(schema.get("paths", {}).keys())
    for expected in ("/health", "/model", "/predict", "/explain"):
        assert expected in paths, f"Missing route: {expected}"


def test_exception_handlers_registered() -> None:
    """create_app() registers exception handlers for domain errors."""
    from backend.app.exceptions import FeatureMissingError, ModelNotAvailableError
    from backend.app.main import create_app

    application = create_app()
    assert ModelNotAvailableError in application.exception_handlers
    assert FeatureMissingError in application.exception_handlers
