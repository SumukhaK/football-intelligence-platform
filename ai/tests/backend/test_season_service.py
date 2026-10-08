"""Tests for backend.app.services.season_service."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from backend.app.services.season_service import (
    SeasonQueryError,
    SeasonService,
    normalise_season,
)
from goals.dixon_coles import DixonColesParams

PL = "Premier League"


def _match(day: str, season: str, home: str, away: str, hg: int, ag: int) -> dict:
    return {
        "match_date": day,
        "season": season,
        "competition": PL,
        "home_team": home,
        "away_team": away,
        "full_time_home_goals": hg,
        "full_time_away_goals": ag,
    }


MATCHES = pd.DataFrame(
    [
        _match("2025-08-20", "2025/26", "Man City", "Man United", 3, 1),
        _match("2026-03-01", "2025/26", "Man United", "Man City", 2, 2),
        _match("2026-08-22", "2026/27", "Man United", "Man City", 0, 1),
        _match("2026-08-29", "2026/27", "Arsenal", "Man United", 2, 0),
    ]
)
SCHEDULE = pd.DataFrame(
    [
        ("2026-10-10", "", "Man City", "Arsenal", "Matchday 7"),
        ("2027-03-20", "2027-03-20T15:00:00+00:00", "Man City", "Man United", "MD 30"),
        # Already in the results: must not be offered as upcoming.
        ("2026-08-29", "", "Arsenal", "Man United", "Matchday 2"),
    ],
    columns=["match_date", "kickoff", "home_team", "away_team", "round"],
)


def _service(today: date = date(2026, 10, 8)) -> SeasonService:
    return SeasonService(MATCHES, today=lambda: today)


def _params() -> DixonColesParams:
    return DixonColesParams(
        competition=PL,
        attack={"Man City": 0.4, "Arsenal": 0.3, "Man United": 0.0},
        defence={"Man City": 0.4, "Arsenal": 0.3, "Man United": 0.0},
        intercept=0.15,
        home_advantage=0.2,
        rho=-0.05,
        newcomer_attack=-0.2,
        newcomer_defence=-0.2,
        fitted_before="2026-10-08",
        n_matches=4,
    )


@pytest.mark.parametrize(
    ("value", "season"),
    [("2026/27", "2026/27"), ("2026-27", "2026/27"), ("2026/2027", "2026/27")],
)
def test_normalise_season_accepts_common_spellings(value: str, season: str) -> None:
    """Seasons may be written several ways."""
    assert normalise_season(value) == season


def test_normalise_season_rejects_non_seasons() -> None:
    """Two years that are not consecutive are not a season."""
    with pytest.raises(SeasonQueryError):
        normalise_season("2026/29")


def test_derby_lists_this_seasons_result_and_next_meeting() -> None:
    """Head-to-head gives this season's meeting and the one still to come."""
    result = _service().team_matches("Man City", PL, SCHEDULE, opponent="Man United")
    assert [r["score"] for r in result["results"]] == ["0-1"]
    assert result["results"][0]["winner"] == "Man City"
    assert [f["date"] for f in result["upcoming"]] == ["2027-03-20"]
    assert "note" not in result


def test_finished_derbies_get_a_note() -> None:
    """With no meeting left, the result says so."""
    schedule = SCHEDULE[SCHEDULE["away_team"] != "Man United"]
    result = _service().team_matches("Man City", PL, schedule, opponent="Man United")
    assert result["upcoming"] == []
    assert "No more meetings" in result["note"]


def test_past_season_results_have_no_fixtures() -> None:
    """A past season lists results, newest first, and no upcoming matches."""
    result = _service().team_matches("Man City", PL, SCHEDULE, season="2025/26")
    assert [r["date"] for r in result["results"]] == ["2026-03-01", "2025-08-20"]
    assert result["results"][0]["winner"] == "draw"
    assert "upcoming" not in result


def test_future_season_is_refused() -> None:
    """Next season has not started, so there is nothing to answer from."""
    with pytest.raises(SeasonQueryError, match="has not started"):
        _service().league_table(PL, SCHEDULE, _params(), season="2027/28")
    with pytest.raises(SeasonQueryError):
        _service().league_table(PL, SCHEDULE, _params(), on=date(2027, 8, 30))


def test_past_season_table_is_actual() -> None:
    """A finished season's table comes from its results."""
    table = _service().league_table(PL, SCHEDULE, None, season="2025/26")
    assert table["kind"] == "actual"
    assert table["table"][0] == {
        "team": "Man City",
        "position": 1,
        "played": 2,
        "won": 1,
        "drawn": 1,
        "lost": 0,
        "goals_for": 5,
        "goals_against": 3,
        "clean_sheets": 0,
        "goal_difference": 2,
        "points": 4,
    }


def test_table_on_a_past_date_ignores_later_results() -> None:
    """The table as of a date only counts matches played by then."""
    table = _service().league_table(PL, SCHEDULE, None, on=date(2026, 8, 25))
    assert table["kind"] == "actual"
    points = {row["team"]: row["points"] for row in table["table"]}
    # Arsenal's first match was on 29 August, after the date asked about.
    assert points == {"Man City": 3, "Man United": 0}


def test_future_date_this_season_is_projected() -> None:
    """A date ahead this season simulates the fixtures up to that date."""
    table = _service().league_table(PL, SCHEDULE, _params(), on=date(2026, 12, 31))
    assert table["kind"] == "projection"
    assert table["fixtures_simulated"] == 1
    teams = {row["team"]: row for row in table["table"]}
    assert teams["Man City"]["current_points"] == 3
    assert teams["Man City"]["expected_points"] > 3


def test_projection_needs_a_goals_model() -> None:
    """Without a fitted goals model there is no projection."""
    with pytest.raises(SeasonQueryError, match="No goals model"):
        _service().league_table(PL, SCHEDULE, None, on=date(2026, 12, 31))
