"""Tests for POST /insights and the insights service."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.exceptions import UnknownTeamError
from backend.app.main import create_app
from backend.app.schemas.insights import InsightsRequest
from backend.app.services.insights_service import (
    InsightsService,
    LeagueGoalsModel,
    load_insights_service,
)
from goals.dixon_coles import DixonColesParams

TEAMS = ["Arsenal", "Chelsea", "Coventry"]


def params() -> DixonColesParams:
    return DixonColesParams(
        competition="Premier League",
        attack={"Arsenal": 0.32, "Chelsea": 0.05},
        defence={"Arsenal": 0.25, "Chelsea": 0.02},
        intercept=0.15,
        home_advantage=0.20,
        rho=-0.08,
        newcomer_attack=-0.25,
        newcomer_defence=-0.30,
        fitted_before="2026-09-28",
        n_matches=1520,
    )


@pytest.fixture()
def service() -> InsightsService:
    return InsightsService(
        {"Premier League": LeagueGoalsModel(params(), "2026/27", frozenset(TEAMS))}
    )


@pytest.fixture()
def insights_client(service: InsightsService) -> TestClient:
    app = create_app()
    app.state.insights_service = service
    return TestClient(app, raise_server_exceptions=False)


def test_insights_returns_scores_and_markets(insights_client: TestClient) -> None:
    response = insights_client.post(
        "/insights", json={"home_team": "Arsenal", "away_team": "Chelsea"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model_version"] == "dc-2026-09-28"
    assert len(body["top_scores"]) == 5
    assert body["expected_goals"]["home"] > body["expected_goals"]["away"]
    outcome = body["outcome"]
    assert outcome["home"] + outcome["draw"] + outcome["away"] == pytest.approx(1.0)
    assert set(body["markets"]) == {
        "btts",
        "over_1_5",
        "over_2_5",
        "over_3_5",
        "home_clean_sheet",
        "away_clean_sheet",
    }
    assert body["reasons"][0].startswith("Arsenal")


def test_promoted_team_without_history_gets_insights(
    insights_client: TestClient,
) -> None:
    response = insights_client.post(
        "/insights", json={"home_team": "Coventry", "away_team": "Arsenal"}
    )
    assert response.status_code == 200
    assert response.json()["outcome"]["away"] > response.json()["outcome"]["home"]


def test_unknown_team_is_422(insights_client: TestClient) -> None:
    response = insights_client.post(
        "/insights", json={"home_team": "Arsenal", "away_team": "Real Madrid"}
    )
    assert response.status_code == 422
    assert response.json()["error"] == "Unknown team"
    assert response.json()["team"] == "Real Madrid"


def test_missing_goals_model_is_503() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.post(
        "/insights", json={"home_team": "Arsenal", "away_team": "Chelsea"}
    )
    assert response.status_code == 503
    assert response.json()["error"] == "Insights not available"


def test_empty_team_is_rejected(insights_client: TestClient) -> None:
    response = insights_client.post(
        "/insights", json={"home_team": "", "away_team": "Chelsea"}
    )
    assert response.status_code == 422


def test_health_reports_insights(insights_client: TestClient) -> None:
    assert insights_client.get("/health").json()["insights_available"] is True


def test_service_rejects_unknown_teams(service: InsightsService) -> None:
    with pytest.raises(UnknownTeamError):
        service.insights(
            InsightsRequest(home_team="Luton", away_team="Arsenal"), "Premier League"
        )


def test_load_fits_on_matches_before_today(tmp_path: Path) -> None:
    rows = []
    teams = ["Arsenal", "Chelsea", "Everton", "Fulham"]
    day = pd.Timestamp("2025-08-01")
    for season in ["2025/26", "2026/27"]:
        for h in teams:
            for a in teams:
                if h != a:
                    rows.append(
                        {
                            "match_date": day.date().isoformat(),
                            "season": season,
                            "competition": "Premier League",
                            "home_team": h,
                            "away_team": a,
                            "full_time_home_goals": 2 if h == "Arsenal" else 1,
                            "full_time_away_goals": 1,
                        }
                    )
                    day += pd.Timedelta(days=7)
    pd.DataFrame(rows).to_csv(
        tmp_path / "match_results_live_v20260928_120000.csv", index=False
    )
    cutoff = date(2026, 1, 1)
    loaded = load_insights_service(
        tmp_path, ["Premier League", "Serie A"], today=cutoff
    )
    assert loaded.model_versions == {"Premier League": "dc-2026-01-01"}
    body = loaded.insights(
        InsightsRequest(home_team="Arsenal", away_team="Fulham"), "Premier League"
    )
    assert body.fitted_before == "2026-01-01"


def test_load_unknown_competition_raises(tmp_path: Path) -> None:
    pd.DataFrame(
        {
            "match_date": ["2026-08-01"],
            "season": ["2026/27"],
            "competition": ["Bundesliga"],
            "home_team": ["A"],
            "away_team": ["B"],
            "full_time_home_goals": [1],
            "full_time_away_goals": [0],
        }
    ).to_csv(tmp_path / "match_results_live_v20260928_120000.csv", index=False)
    with pytest.raises(KeyError):
        load_insights_service(tmp_path, ["Premier League"])
