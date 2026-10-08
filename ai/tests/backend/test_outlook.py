"""Tests for GET /v2/teams/{team}/outlook (ADR 023)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.services.insights_service import InsightsService, LeagueGoalsModel
from backend.app.services.outlook_service import OutlookService
from tests.backend.test_outlook_service import MATCHES, PL, SIMS, TEAMS, TODAY
from tests.backend.test_outlook_service import _params as fitted_params
from tests.backend.test_outlook_service import _schedule as schedule

URL = "/v2/teams/Arsenal/outlook"


def _insights() -> InsightsService:
    league = LeagueGoalsModel(fitted_params(), "2026/27", frozenset(TEAMS))
    return InsightsService({PL: league})


def _fixtures() -> MagicMock:
    fixtures = MagicMock()
    fixtures.schedule.return_value = schedule()
    return fixtures


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    app.state.outlook_service = OutlookService(
        MATCHES, today=lambda: TODAY, history_simulations=SIMS
    )
    app.state.insights_service = _insights()
    app.state.fixtures_service = _fixtures()
    return TestClient(app, raise_server_exceptions=False)


def test_outlook_returns_projection_table_and_history(client: TestClient) -> None:
    response = client.get(URL, params={"competition": PL})
    assert response.status_code == 200
    body = response.json()
    assert body["team"] == "Arsenal"
    assert body["projection"]["current_points"] == 6
    assert set(body["projection"]) >= {
        "most_likely_position",
        "expected_points",
        "chance_first",
        "chance_top_four",
        "chance_bottom_three",
    }
    assert {row["team"] for row in body["table"]} == set(TEAMS)
    assert [p["played"] for p in body["history"]] == [0, 1, 1]
    assert body["simulations"] == 10_000
    assert body["history_simulations"] == SIMS
    assert body["strengths"]["attack"] > 0


def test_outlook_defaults_to_the_premier_league(client: TestClient) -> None:
    assert client.get(URL).json()["competition"] == PL


def test_unknown_team_is_422(client: TestClient) -> None:
    response = client.get("/v2/teams/Real%20Madrid/outlook")
    assert response.status_code == 422
    assert response.json()["error"] == "Unknown team"


def test_unserved_league_is_422(client: TestClient) -> None:
    response = client.get(URL, params={"competition": "Eredivisie"})
    assert response.status_code == 422
    assert response.json()["error"] == "Unknown competition"


def test_without_match_history_it_is_503(client: TestClient) -> None:
    client.app.state.outlook_service = None  # type: ignore[attr-defined]
    response = client.get(URL)
    assert response.status_code == 503
    assert response.json()["error"] == "Season outlook not available"


def test_without_a_goals_model_for_the_league_it_is_503(client: TestClient) -> None:
    client.app.state.insights_service = InsightsService({})  # type: ignore[attr-defined]
    response = client.get(URL, params={"competition": "Serie A"})
    assert response.status_code == 503
    assert response.json()["error"] == "Insights not available"


def test_without_fixtures_it_is_503(client: TestClient) -> None:
    client.app.state.fixtures_service = None  # type: ignore[attr-defined]
    assert client.get(URL).status_code == 503


def test_v1_has_no_outlook(client: TestClient) -> None:
    assert client.get("/v1/teams/Arsenal/outlook").status_code == 404
