"""Tests for backend.app.services.season_tools."""

from __future__ import annotations

import json
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

from assistant.tools.tool import run_tool
from backend.app.services.competitions import ServedCompetitions
from backend.app.services.season_service import SeasonService
from backend.app.services.season_tools import SeasonTools
from tests.backend.test_season_service import MATCHES, SCHEDULE, _params

LEAGUES = ServedCompetitions(("Premier League", "Bundesliga"), "Premier League")


def _state(**overrides: object) -> SimpleNamespace:
    fixtures = MagicMock()
    fixtures.schedule.return_value = SCHEDULE
    insights = MagicMock()
    insights.params.return_value = _params()
    state = {
        "season_service": SeasonService(MATCHES, today=lambda: date(2026, 10, 8)),
        "fixtures_service": fixtures,
        "insights_service": insights,
    }
    return SimpleNamespace(**{**state, **overrides})


def _call(state: SimpleNamespace, name: str, **args: object) -> dict[str, object]:
    tools = SeasonTools(state, LEAGUES).tools()
    result: dict[str, object] = json.loads(run_tool(tools, name, args))
    return result


def test_team_matches_resolves_full_club_names() -> None:
    """ "Manchester City" finds Man City and its next derby."""
    result = _call(
        _state(), "team_matches", team="Manchester City", opponent="Manchester United"
    )
    assert result["team"] == "Man City"
    assert result["opponent"] == "Man United"
    assert result["competition"] == "Premier League"


def test_league_table_projects_a_future_date() -> None:
    """A date later this season uses the goals model."""
    result = _call(_state(), "league_table", date="2026-12-26")
    assert result["kind"] == "projection"


def test_errors_reach_the_model_as_tool_errors() -> None:
    """Bad dates, future seasons and unknown teams come back as messages."""
    assert "YYYY-MM-DD" in str(
        _call(_state(), "league_table", date="Boxing Day")["error"]
    )
    assert "has not started" in str(
        _call(_state(), "league_table", season="2027/28")["error"]
    )
    assert "Atlantis" in str(_call(_state(), "team_matches", team="Atlantis")["error"])


def test_missing_history_is_reported() -> None:
    """Without match history the tool says so instead of failing the chat."""
    result = _call(_state(season_service=None), "team_matches", team="Arsenal")
    assert "not loaded" in str(result["error"])


def test_missing_fixtures_still_answer_results() -> None:
    """Without the fixtures dataset, results are listed and nothing is upcoming."""
    result = _call(_state(fixtures_service=None), "team_matches", team="Arsenal")
    assert result["upcoming"] == []
    assert len(result["results"]) == 1  # type: ignore[arg-type]
