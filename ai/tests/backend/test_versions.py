"""Tests for API versions (ADR 014): v1 keeps the v1.0.0 contract, v2 is current."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.services.fixture_feature_service import FixtureFeatureService
from tests.backend.conftest import make_explanation_response, make_prediction_response
from tests.backend.test_fixture_features import service  # noqa: F401 — fixture


@pytest.fixture()
def versioned_client(service: FixtureFeatureService) -> Any:  # noqa: F811
    """v1 and v2 backed by different mock models."""
    app = create_app()
    v1_prediction = MagicMock()
    v1_prediction.predict.return_value = make_prediction_response().model_copy(
        update={"model_version": "20260630_132617", "competition": "Premier League"}
    )
    v1_explanation = MagicMock()
    v1_explanation.explain.return_value = make_explanation_response()
    v2_prediction = MagicMock()
    v2_prediction.predict.return_value = make_prediction_response().model_copy(
        update={"model_version": "20260928_123224"}
    )
    app.state.v1_prediction_service = v1_prediction
    app.state.v1_explanation_service = v1_explanation
    app.state.prediction_service = v2_prediction
    app.state.fixture_feature_service = service
    return TestClient(app, raise_server_exceptions=False)


FIXTURE = {"home_team": "Arsenal", "away_team": "Chelsea"}


@pytest.mark.parametrize("path", ["/predict", "/v1/predict"])
def test_v1_and_unversioned_use_the_original_model(
    versioned_client: TestClient, path: str
) -> None:
    body = versioned_client.post(path, json=FIXTURE).json()
    assert body["model_version"] == "20260630_132617"


@pytest.mark.parametrize("path", ["/predict", "/v1/predict"])
def test_v1_responses_have_only_the_original_fields(
    versioned_client: TestClient, path: str
) -> None:
    body = versioned_client.post(path, json=FIXTURE).json()
    assert "competition" not in body
    assert "draw_possible" not in body


def test_v2_uses_the_current_model(versioned_client: TestClient) -> None:
    body = versioned_client.post("/v2/predict", json=FIXTURE).json()
    assert body["model_version"] == "20260928_123224"
    assert body["competition"] == "Premier League"
    assert "draw_possible" in body


def test_v1_is_premier_league_only(versioned_client: TestClient) -> None:
    response = versioned_client.post(
        "/v1/predict", json={**FIXTURE, "competition": "Bundesliga"}
    )
    assert response.status_code == 422
    assert response.json()["supported"] == ["Premier League"]


def test_v1_explanations_drop_display_labels(versioned_client: TestClient) -> None:
    body = versioned_client.post("/explain", json=FIXTURE).json()
    assert "competition" not in body
    for feature in body["all_contributions"]:
        assert "display_name" not in feature


def test_v1_teams_are_the_premier_league(versioned_client: TestClient) -> None:
    assert versioned_client.get("/teams").json()["competition"] == "Premier League"


@pytest.mark.parametrize("path", ["/v1/competitions", "/competitions", "/v1/insights"])
def test_new_endpoints_exist_only_in_v2(
    versioned_client: TestClient, path: str
) -> None:
    method = (
        versioned_client.post if path.endswith("insights") else versioned_client.get
    )
    assert method(path).status_code in (404, 405)


def test_health_is_available_in_every_version(versioned_client: TestClient) -> None:
    for path in ["/health", "/v1/health", "/v2/health"]:
        assert versioned_client.get(path).status_code == 200


def test_docs_list_v1_and_v2_but_not_unversioned_paths() -> None:
    paths = TestClient(create_app()).get("/openapi.json").json()["paths"]
    assert "/v1/predict" in paths
    assert "/v2/predict" in paths
    assert "/predict" not in paths
