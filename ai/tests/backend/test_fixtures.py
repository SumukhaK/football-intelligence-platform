"""Tests for the upcoming fixtures service and GET /v2/fixtures (ADR 015)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.services.fixtures_service import FixturesService

ROWS = [
    ("Premier League", "2026-09-27", "", "Liverpool", "Everton"),
    ("Premier League", "2026-10-10", "", "Man City", "Fulham"),
    ("Premier League", "2026-10-10", "2026-10-10T17:30:00+01:00", "Chelsea", "Spurs"),
    ("Premier League", "2026-10-10", "2026-10-10T12:30:00+01:00", "Arsenal", "Leeds"),
    ("Premier League", "2026-10-18", "", "Everton", "Brentford"),
    ("Bundesliga", "2026-10-09", "2026-10-09T20:30:00+02:00", "Dortmund", "Mainz"),
]


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "competition": c,
                "match_date": d,
                "kickoff": k,
                "home_team": h,
                "away_team": a,
                "round": "Matchday 6",
            }
            for c, d, k, h, a in ROWS
        ]
    )


@pytest.fixture()
def service() -> FixturesService:
    return FixturesService(_frame(), today=lambda: date(2026, 9, 29))


def test_past_fixtures_are_left_out(service: FixturesService) -> None:
    homes = [f.home_team for f in service.upcoming("Premier League", 50).fixtures]
    assert "Liverpool" not in homes


def test_fixtures_are_in_kickoff_order_with_unknown_times_last(
    service: FixturesService,
) -> None:
    homes = [f.home_team for f in service.upcoming("Premier League", 50).fixtures]
    assert homes == ["Arsenal", "Chelsea", "Man City", "Everton"]


def test_limit_caps_the_list(service: FixturesService) -> None:
    assert len(service.upcoming("Premier League", 2).fixtures) == 2


def test_only_the_requested_league(service: FixturesService) -> None:
    fixtures = service.upcoming("Bundesliga", 50).fixtures
    assert [f.home_team for f in fixtures] == ["Dortmund"]
    assert fixtures[0].kickoff is not None


def test_from_directory_reads_the_newest_file(tmp_path: Path) -> None:
    _frame().head(1).to_csv(tmp_path / "fixtures_v20260901_000000.csv", index=False)
    _frame().to_csv(tmp_path / "fixtures_v20260929_070000.csv", index=False)
    loaded = FixturesService.from_directory(tmp_path, lambda: date(2026, 9, 29))
    assert len(loaded.upcoming("Premier League", 50).fixtures) == 4
    assert loaded.updated_at is not None
    assert loaded.updated_at.day == 29


def test_from_directory_without_data_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        FixturesService.from_directory(tmp_path, date.today)


@pytest.fixture()
def api(service: FixturesService) -> Any:
    app = create_app()
    app.state.fixtures_service = service
    return TestClient(app, raise_server_exceptions=False)


def test_endpoint_defaults_to_the_premier_league(api: TestClient) -> None:
    body = api.get("/v2/fixtures").json()
    assert body["competition"] == "Premier League"
    assert body["fixtures"][0] == {
        "match_date": "2026-10-10",
        "kickoff": "2026-10-10T12:30:00+01:00",
        "home_team": "Arsenal",
        "away_team": "Leeds",
        "round": "Matchday 6",
    }


def test_endpoint_filters_by_league(api: TestClient) -> None:
    body = api.get("/v2/fixtures", params={"competition": "Bundesliga"}).json()
    assert [f["home_team"] for f in body["fixtures"]] == ["Dortmund"]


def test_endpoint_rejects_an_unknown_league(api: TestClient) -> None:
    response = api.get("/v2/fixtures", params={"competition": "Eredivisie"})
    assert response.status_code == 422
    assert response.json()["error"] == "Unknown competition"


def test_endpoint_without_fixtures_is_503() -> None:
    app = create_app()
    app.state.fixtures_service = None
    response = TestClient(app).get("/v2/fixtures")
    assert response.status_code == 503
    assert response.json()["error"] == "Fixtures not available"


def test_fixtures_are_v2_only(api: TestClient) -> None:
    assert api.get("/v1/fixtures").status_code == 404
    assert api.get("/fixtures").status_code == 404
