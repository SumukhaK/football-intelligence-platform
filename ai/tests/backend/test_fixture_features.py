"""Tests for server-side fixture features: service, /teams, /predict, /explain."""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.exceptions import FixtureFeaturesNotAvailableError, UnknownTeamError
from backend.app.main import create_app
from backend.app.schemas.prediction import PredictionRequest
from backend.app.services.fixture_feature_service import (
    FixtureFeatureService,
    resolve_features,
)
from inference.fixture_features import FixtureFeatureBuilder

_COMP = "Premier League"


def _row(day: str, season: str, home: str, away: str, res: str) -> dict[str, Any]:
    goals = {"H": (2, 0), "D": (1, 1), "A": (0, 1)}[res]
    return {
        "match_date": day,
        "season": season,
        "competition": _COMP,
        "home_team": home,
        "away_team": away,
        "full_time_home_goals": goals[0],
        "full_time_away_goals": goals[1],
        "result": res,
    }


@pytest.fixture()
def service() -> FixtureFeatureService:
    matches = pd.DataFrame(
        [
            _row("2025-08-16", "2025/26", "Arsenal", "Leeds", "H"),
            _row("2025-08-16", "2025/26", "Chelsea", "Burnley", "D"),
            _row("2026-08-22", "2026/27", "Leeds", "Chelsea", "A"),
            _row("2026-08-22", "2026/27", "Arsenal", "Sunderland", "H"),
        ]
    )
    return FixtureFeatureService(
        FixtureFeatureBuilder(matches), _COMP, today=lambda: date(2026, 9, 28)
    )


def _request(**kwargs: Any) -> PredictionRequest:
    return PredictionRequest(home_team="Arsenal", away_team="Chelsea", **kwargs)


class TestFixtureFeatureService:
    def test_supplied_features_pass_through(
        self, service: FixtureFeatureService
    ) -> None:
        assert service.features_for(_request(features={"x": 1.0})) == {"x": 1.0}

    def test_features_are_computed_from_history(
        self, service: FixtureFeatureService
    ) -> None:
        features = service.features_for(_request())
        assert len(features) == 42
        assert features["h2h_meetings"] == 0
        assert features["home_league_points"] == 3
        assert features["away_league_points"] == 3

    def test_match_date_limits_history(self, service: FixtureFeatureService) -> None:
        features = service.features_for(_request(match_date=date(2026, 8, 20)))
        assert features["home_league_points"] == 0

    def test_unknown_team_raises(self, service: FixtureFeatureService) -> None:
        with pytest.raises(UnknownTeamError) as err:
            service.features_for(
                PredictionRequest(home_team="Burnley", away_team="Arsenal")
            )
        assert err.value.team == "Burnley"
        assert err.value.season == "2026/27"

    def test_teams_are_the_latest_season(self, service: FixtureFeatureService) -> None:
        response = service.teams()
        assert response.season == "2026/27"
        assert response.teams == ["Arsenal", "Chelsea", "Leeds", "Sunderland"]

    def test_resolve_without_service_needs_features(self) -> None:
        assert resolve_features(_request(features={"x": 1.0}), None) == {"x": 1.0}
        with pytest.raises(FixtureFeaturesNotAvailableError):
            resolve_features(_request(), None)


@pytest.fixture()
def fixture_client(
    service: FixtureFeatureService,
    mock_prediction_service: MagicMock,
    mock_explanation_service: MagicMock,
) -> TestClient:
    application = create_app()
    application.state.prediction_service = mock_prediction_service
    application.state.explanation_service = mock_explanation_service
    application.state.fixture_feature_service = service
    return TestClient(application, raise_server_exceptions=False)


class TestEndpoints:
    def test_teams(self, fixture_client: TestClient) -> None:
        body = fixture_client.get("/teams").json()
        assert body == {
            "competition": _COMP,
            "season": "2026/27",
            "teams": ["Arsenal", "Chelsea", "Leeds", "Sunderland"],
        }

    def test_teams_503_without_history(self, client: TestClient) -> None:
        response = client.get("/teams")
        assert response.status_code == 503
        assert response.json()["error"] == "Match features not available"

    def test_predict_without_features_uses_computed_features(
        self, fixture_client: TestClient, mock_prediction_service: MagicMock
    ) -> None:
        response = fixture_client.post(
            "/predict", json={"home_team": "Arsenal", "away_team": "Chelsea"}
        )
        assert response.status_code == 200
        sent = mock_prediction_service.predict.call_args.args[0]
        assert sent.features["home_league_points"] == 3
        assert len(sent.features) == 42

    def test_explain_without_features_uses_computed_features(
        self, fixture_client: TestClient, mock_explanation_service: MagicMock
    ) -> None:
        response = fixture_client.post(
            "/explain",
            json={
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "match_date": "2026-08-20",
            },
        )
        assert response.status_code == 200
        features = mock_explanation_service.explain.call_args.kwargs["features"]
        assert features["home_league_points"] == 0

    def test_unknown_team_is_a_structured_422(self, fixture_client: TestClient) -> None:
        response = fixture_client.post(
            "/predict", json={"home_team": "Luton", "away_team": "Arsenal"}
        )
        assert response.status_code == 422
        assert response.json() == {
            "error": "Unknown team",
            "detail": "'Luton' did not play in Premier League 2026/27",
            "team": "Luton",
        }

    def test_health_reports_fixture_features(
        self, fixture_client: TestClient, client: TestClient
    ) -> None:
        assert fixture_client.get("/health").json()["fixture_features_available"]
        assert not client.get("/health").json()["fixture_features_available"]
