"""Tests for serving several leagues (ADR 012)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.exceptions import UnknownCompetitionError, UnknownTeamError
from backend.app.main import create_app
from backend.app.schemas.prediction import PredictionRequest
from backend.app.services.competitions import ServedCompetitions
from backend.app.services.fixture_feature_service import FixtureFeatureService
from backend.app.services.insights_service import InsightsService, LeagueGoalsModel
from goals.dixon_coles import DixonColesParams
from tests.backend.test_fixture_features import service  # noqa: F401 — fixture

SERVED = ServedCompetitions(("Premier League", "Bundesliga"), "Premier League")


def goals_model(competition: str, teams: list[str]) -> LeagueGoalsModel:
    params = DixonColesParams(
        competition=competition,
        attack=dict.fromkeys(teams, 0.0),
        defence=dict.fromkeys(teams, 0.0),
        intercept=0.3,
        home_advantage=0.2,
        rho=-0.05,
        newcomer_attack=-0.2,
        newcomer_defence=-0.2,
        fitted_before="2026-09-28",
        n_matches=300,
    )
    return LeagueGoalsModel(params, "2026/27", frozenset(teams))


@pytest.fixture()
def league_client(
    service: FixtureFeatureService,  # noqa: F811
    mock_prediction_service: MagicMock,
    mock_explanation_service: MagicMock,
) -> TestClient:
    app = create_app()
    app.state.prediction_service = mock_prediction_service
    app.state.explanation_service = mock_explanation_service
    app.state.fixture_feature_service = service
    app.state.insights_service = InsightsService(
        {"Bundesliga": goals_model("Bundesliga", ["Bayern", "Leipzig", "Dortmund"])}
    )
    return TestClient(app, raise_server_exceptions=False)


class TestServedCompetitions:
    def test_missing_league_means_the_default(self) -> None:
        assert SERVED.resolve(None) == "Premier League"

    def test_served_league_is_accepted(self) -> None:
        assert SERVED.resolve("Bundesliga") == "Bundesliga"

    def test_unknown_league_is_rejected(self) -> None:
        with pytest.raises(UnknownCompetitionError) as err:
            SERVED.resolve("Eredivisie")
        assert err.value.supported == ["Premier League", "Bundesliga"]


class TestLeagueServices:
    def test_features_for_a_second_league(
        self, service: FixtureFeatureService  # noqa: F811
    ) -> None:
        request = PredictionRequest(home_team="Bayern", away_team="Leipzig")
        features = service.features_for(request, "Bundesliga")
        assert features["home_league_points"] == 3

    def test_team_from_another_league_is_rejected(
        self, service: FixtureFeatureService  # noqa: F811
    ) -> None:
        request = PredictionRequest(home_team="Arsenal", away_team="Bayern")
        with pytest.raises(UnknownTeamError) as err:
            service.features_for(request, "Bundesliga")
        assert err.value.competition == "Bundesliga"


def _post(client: TestClient, path: str, **body: Any) -> Any:
    return client.post(
        path, json={"home_team": "Bayern", "away_team": "Leipzig", **body}
    )


class TestEndpoints:
    def test_competitions_lists_leagues_with_history(
        self, league_client: TestClient
    ) -> None:
        body = league_client.get("/v2/competitions").json()
        assert body["default"] == "Premier League"
        by_name = {c["name"]: c for c in body["competitions"]}
        assert by_name["Bundesliga"] == {
            "name": "Bundesliga",
            "season": "2026/27",
            "team_count": 4,
            "matches_through": "2026-08-29",
            "insights_available": True,
        }
        assert by_name["Premier League"]["insights_available"] is False
        # Served by default but absent from the test history, so left out.
        assert "Serie A" not in by_name

    def test_teams_for_a_league(self, league_client: TestClient) -> None:
        body = league_client.get(
            "/v2/teams", params={"competition": "Bundesliga"}
        ).json()
        assert body["competition"] == "Bundesliga"
        assert body["teams"] == ["Bayern", "Dortmund", "Freiburg", "Leipzig"]

    def test_teams_default_to_the_premier_league(
        self, league_client: TestClient
    ) -> None:
        assert league_client.get("/v2/teams").json()["competition"] == "Premier League"

    def test_unknown_league_is_a_structured_422(
        self, league_client: TestClient
    ) -> None:
        response = _post(league_client, "/v2/predict", competition="Eredivisie")
        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "Unknown competition"
        assert body["competition"] == "Eredivisie"
        assert "Bundesliga" in body["supported"]

    def test_predict_uses_and_echoes_the_league(
        self, league_client: TestClient, mock_prediction_service: MagicMock
    ) -> None:
        response = _post(league_client, "/v2/predict", competition="Bundesliga")
        assert response.status_code == 200
        assert response.json()["competition"] == "Bundesliga"
        sent = mock_prediction_service.predict.call_args.args[0]
        assert sent.features["home_league_points"] == 3

    def test_predict_without_a_league_is_the_premier_league(
        self, league_client: TestClient
    ) -> None:
        response = league_client.post(
            "/v2/predict", json={"home_team": "Arsenal", "away_team": "Chelsea"}
        )
        assert response.json()["competition"] == "Premier League"

    def test_explain_echoes_the_league(self, league_client: TestClient) -> None:
        response = _post(league_client, "/v2/explain", competition="Bundesliga")
        assert response.status_code == 200
        assert response.json()["competition"] == "Bundesliga"

    def test_insights_for_a_league(self, league_client: TestClient) -> None:
        response = _post(league_client, "/v2/insights", competition="Bundesliga")
        assert response.status_code == 200
        assert response.json()["competition"] == "Bundesliga"

    def test_insights_for_a_league_without_a_model_is_503(
        self, league_client: TestClient
    ) -> None:
        response = league_client.post(
            "/v2/insights", json={"home_team": "Arsenal", "away_team": "Chelsea"}
        )
        assert response.status_code == 503
        assert response.json()["error"] == "Insights not available"
