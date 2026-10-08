"""Tests for backend.app.services.assistant_tools."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from assistant.tools.tool import Tool, ToolError, run_tool
from backend.app.exceptions import UnknownTeamError
from backend.app.schemas.fixtures import Fixture, FixturesResponse
from backend.app.services.assistant_tools import AssistantTools
from backend.app.services.competitions import ServedCompetitions
from tests.backend.conftest import make_explanation_response, make_prediction_response

FEATURES = {"home_elo": 1550.0, "away_elo": 1480.0}
LEAGUES = ServedCompetitions(("Premier League", "Bundesliga"), "Premier League")


def _state() -> SimpleNamespace:
    prediction = MagicMock()
    prediction.predict.return_value = make_prediction_response()
    explanation = MagicMock()
    explanation.explain.return_value = make_explanation_response()
    features = MagicMock()
    features.features_for.return_value = FEATURES
    fixtures = MagicMock()
    fixtures.upcoming.return_value = FixturesResponse(
        competition="Bundesliga",
        fixtures=[
            Fixture(
                match_date=date(2026, 10, 10),
                home_team="Bayern Munich",
                away_team="Dortmund",
                round="Matchday 7",
            )
        ],
        updated_at=datetime(2026, 10, 7, tzinfo=UTC),
    )
    return SimpleNamespace(
        prediction_service=prediction,
        explanation_service=explanation,
        fixture_feature_service=features,
        fixtures_service=fixtures,
    )


def _tools(state: SimpleNamespace) -> list[Tool]:
    return AssistantTools(state, LEAGUES).tools()


def _call(state: SimpleNamespace, name: str, **args: object) -> dict[str, object]:
    result: dict[str, object] = json.loads(run_tool(_tools(state), name, args))
    return result


def test_tools_are_named_for_the_endpoints() -> None:
    """The assistant is offered the API tools and the season tools."""
    names = [tool.name for tool in _tools(_state())]
    assert names == [
        "predict_match",
        "explain_match",
        "upcoming_fixtures",
        "team_matches",
        "league_table",
    ]


def test_predict_match_returns_the_prediction_service_output() -> None:
    """predict_match quotes the service's response, with the resolved league."""
    state = _state()
    result = _call(state, "predict_match", home_team="Arsenal", away_team="Chelsea")

    expected = make_prediction_response().model_dump(mode="json")
    assert result == {**expected, "competition": "Premier League"}
    sent = state.prediction_service.predict.call_args.args[0]
    assert sent.features == FEATURES


def test_explain_match_drops_the_full_contribution_list() -> None:
    """explain_match keeps the top contributors and omits all_contributions."""
    state = _state()
    result = _call(
        state,
        "explain_match",
        home_team="Arsenal",
        away_team="Chelsea",
        competition="Premier League",
    )
    assert "all_contributions" not in result
    assert result["top_positive_features"]
    state.explanation_service.explain.assert_called_once_with(
        "Arsenal", "Chelsea", FEATURES
    )


def test_upcoming_fixtures_clamps_the_limit() -> None:
    """upcoming_fixtures resolves the league and caps the number of matches."""
    state = _state()
    result = _call(state, "upcoming_fixtures", competition="Bundesliga", limit=500)
    assert result["fixtures"][0]["home_team"] == "Bayern Munich"  # type: ignore[index]
    state.fixtures_service.upcoming.assert_called_once_with("Bundesliga", 20)


@pytest.mark.parametrize(
    ("name", "args", "message"),
    [
        ("predict_match", {"home_team": "Arsenal"}, "away_team"),
        (
            "predict_match",
            {"home_team": "Arsenal", "away_team": "Leeds", "competition": "MLS"},
            "'MLS' is not served",
        ),
        ("upcoming_fixtures", {"limit": "many"}, "limit must be a whole number"),
    ],
)
def test_bad_arguments_come_back_as_tool_errors(
    name: str, args: dict[str, object], message: str
) -> None:
    """Arguments the API would reject are reported to the model, not raised."""
    assert message in str(_call(_state(), name, **args)["error"])


def test_unknown_team_comes_back_as_a_tool_error() -> None:
    """A team outside the league's season is reported to the model."""
    state = _state()
    state.fixture_feature_service.features_for.side_effect = UnknownTeamError(
        "Atlantis", "Premier League", "2026-2027"
    )
    result = _call(state, "predict_match", home_team="Atlantis", away_team="Leeds")
    assert result == {"error": "'Atlantis' did not play in Premier League 2026-2027"}


def test_missing_service_is_a_tool_error() -> None:
    """A model that failed to load is reported, so the assistant can say so."""
    state = _state()
    state.prediction_service = None
    tool = _tools(state)[0]
    with pytest.raises(ToolError, match="Prediction model is not loaded"):
        tool.handler({"home_team": "Arsenal", "away_team": "Leeds"})


def test_predict_match_maps_full_club_names() -> None:
    """Names as users type them reach the model as the data's names."""
    state = _state()
    state.season_service = MagicMock()
    state.season_service.teams.return_value = ["Man City", "Man United"]
    _call(state, "predict_match", home_team="Manchester City", away_team="Man United")
    sent = state.prediction_service.predict.call_args.args[0]
    assert (sent.home_team, sent.away_team) == ("Man City", "Man United")


def test_tool_results_round_probabilities() -> None:
    """Long floats are rounded so small models don't truncate them."""
    state = _state()
    state.prediction_service.predict.return_value = make_prediction_response(
        prob_home=0.6499661, prob_draw=0.2269321, prob_away=0.1231018
    )
    result = _call(state, "predict_match", home_team="Arsenal", away_team="Chelsea")
    assert (result["probability_home"], result["probability_draw"]) == (0.65, 0.227)
