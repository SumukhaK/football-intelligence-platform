"""Tests for backend.app.services.season_router."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
import pytest

from assistant.generation.generator import ToolCall
from backend.app.services.competitions import ServedCompetitions
from backend.app.services.season_router import (
    FUTURE_SEASON_REPLY,
    PLAYER_REPLY,
    SeasonRouter,
)
from backend.app.services.season_service import SeasonService
from tests.backend.test_season_service import MATCHES, SCHEDULE

LEAGUES = ServedCompetitions(("Premier League", "Bundesliga"), "Premier League")
PL = {"competition": "Premier League"}


def _router(**overrides: object) -> SeasonRouter:
    fixtures = MagicMock()
    fixtures.schedule.return_value = SCHEDULE
    state = {
        "season_service": SeasonService(MATCHES, today=lambda: date(2026, 10, 8)),
        "fixtures_service": fixtures,
    }
    return SeasonRouter(SimpleNamespace(**{**state, **overrides}), LEAGUES)


def _calls(question: str) -> list[ToolCall]:
    route = _router().route(question)
    assert route is not None and route.reply is None
    return route.calls


@pytest.mark.parametrize(
    "question",
    ["Who will be the Premier League's top scorer?", "Who has the most assists?"],
)
def test_player_questions_get_a_fixed_reply(question: str) -> None:
    """Player questions are answered without the model: there is no player data."""
    route = _router().route(question)
    assert route is not None and route.reply == PLAYER_REPLY


def test_next_season_gets_a_fixed_reply() -> None:
    """A season that has not started is refused without the model."""
    route = _router().route("Who will win the Premier League next season?")
    expected = FUTURE_SEASON_REPLY.format(current="2026/27", season="2027/28")
    assert route is not None and route.reply == expected


@pytest.mark.parametrize(
    ("question", "date_arg"),
    [
        ("Who will top the Premier League after Boxing Day?", "2026-12-27"),
        ("Who tops the Premier League on Valentine's Day?", "2027-02-14"),
        ("Premier League table on 3 January", "2027-01-03"),
        ("Who is top of the Premier League at the end of November?", "2026-11-30"),
        ("Who will win the Premier League?", "end"),
        ("Which Premier League team will score the most goals?", "end"),
    ],
)
def test_table_questions_pick_the_date(question: str, date_arg: str) -> None:
    """Holidays, dates and season-end questions become a league_table date."""
    assert _calls(question) == [ToolCall("league_table", {**PL, "date": date_arg})]


def test_past_season_uses_the_final_table() -> None:
    """ "Who won in 2025/26" asks for that season's table, with no date."""
    calls = _calls("Who won the Premier League in 2025/26?")
    assert calls == [ToolCall("league_table", {**PL, "season": "2025/26"})]


def test_one_team_and_the_league_question_uses_its_league() -> None:
    """A team's name is enough to know which league's table to read."""
    calls = _calls("Will Arsenal win the league?")
    assert calls == [ToolCall("league_table", {**PL, "date": "end"})]


def test_derby_lists_meetings_and_predicts_the_next_one() -> None:
    """A named derby becomes head-to-head plus a prediction of the next meeting."""
    calls = _calls("Who wins the next Manchester derby?")
    assert calls == [
        ToolCall("team_matches", {"team": "Man City", **PL, "opponent": "Man United"}),
        ToolCall(
            "predict_match",
            {"home_team": "Man City", "away_team": "Man United", **PL},
        ),
    ]


def test_full_club_names_are_recognised() -> None:
    """ "Manchester United" in a question is the data's "Man United"."""
    calls = _calls("When do Manchester United play Arsenal again?")
    assert calls[0] == ToolCall(
        "team_matches", {"team": "Man United", **PL, "opponent": "Arsenal"}
    )


def test_team_results_question() -> None:
    """One team and a results word lists that team's matches."""
    assert _calls("How did Arsenal do recently?") == [
        ToolCall("team_matches", {"team": "Arsenal", **PL})
    ]


def test_no_prediction_without_a_next_fixture() -> None:
    """With nothing left to play, only the results are fetched."""
    schedule = pd.DataFrame(columns=SCHEDULE.columns)
    fixtures = MagicMock()
    fixtures.schedule.return_value = schedule
    route = _router(fixtures_service=fixtures).route(
        "Will Arsenal win their next game?"
    )
    assert route is not None
    assert [call.name for call in route.calls] == ["team_matches"]


@pytest.mark.parametrize(
    "question",
    ["What was the model's test accuracy?", "Explain how SHAP values work."],
)
def test_platform_questions_go_to_the_model(question: str) -> None:
    """Questions about the platform itself are not routed."""
    assert _router().route(question) is None


def test_no_history_means_no_routing() -> None:
    """Without match history the model handles everything, as before."""
    assert _router(season_service=None).route("Who won the league?") is None
