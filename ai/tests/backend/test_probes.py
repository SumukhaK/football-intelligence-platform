"""Tests for GET /v2/live and GET /v2/ready (ADR 025)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.services.readiness import REQUIRED_COMPONENTS, missing_components


def _all_loaded() -> SimpleNamespace:
    return SimpleNamespace(
        **{attr: MagicMock() for attr in REQUIRED_COMPONENTS.values()}
    )


def _client(state: SimpleNamespace) -> TestClient:
    application = create_app()
    for attr, value in vars(state).items():
        setattr(application.state, attr, value)
    return TestClient(application, raise_server_exceptions=False)


def test_missing_components_empty_when_all_loaded() -> None:
    """Nothing is missing when every required service is set."""
    assert missing_components(_all_loaded()) == []


def test_missing_components_names_each_unloaded_component() -> None:
    """A None or absent service is reported by its component name."""
    state = _all_loaded()
    state.prediction_service = None
    del state.fixtures_service
    assert missing_components(state) == ["prediction_model", "fixtures"]


def test_live_answers_while_nothing_is_loaded() -> None:
    """Liveness only says the process serves requests."""
    response = _client(SimpleNamespace()).get("/v2/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_ready_when_all_components_loaded() -> None:
    """Readiness is 200 once every required component loaded."""
    response = _client(_all_loaded()).get("/v2/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_not_ready_lists_missing_components() -> None:
    """A missing model gives a structured 503 that names it."""
    state = _all_loaded()
    state.prediction_service = None
    response = _client(state).get("/v2/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["error"] == "Not ready"
    assert "prediction_model" in body["detail"]


@pytest.mark.parametrize("path", ["/v2/live", "/v2/ready"])
def test_probes_are_never_rate_limited(
    path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Probes stay open however often the platform calls them."""
    from backend.app.config import Settings

    settings = Settings(rate_limit_per_minute=1)
    monkeypatch.setattr("backend.app.config._settings", settings)
    monkeypatch.setattr("backend.app.main.get_settings", lambda: settings)
    client = _client(_all_loaded())
    assert all(client.get(path).status_code == 200 for _ in range(3))


@pytest.mark.parametrize("path", ["/live", "/v1/live", "/ready", "/v1/ready"])
def test_probes_exist_only_under_v2(path: str) -> None:
    """Probes are new, so older API versions do not get them."""
    assert _client(_all_loaded()).get(path).status_code == 404
