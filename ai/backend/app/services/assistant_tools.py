"""Assistant tools backed by the API's own services (ADR 018).

Each tool runs the same service code as its endpoint, so the assistant quotes
exactly what POST /v2/predict, POST /v2/explain and GET /v2/fixtures return. Services
are read from ``app.state`` at call time because the daily refresh swaps them.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from assistant.tools.tool import Tool, ToolError, ToolHandler
from backend.app.exceptions import (
    FeatureMissingError,
    FixtureFeaturesNotAvailableError,
    FixturesNotAvailableError,
    ModelNotAvailableError,
    UnknownCompetitionError,
    UnknownTeamError,
)
from backend.app.schemas.prediction import PredictionRequest
from backend.app.services.competitions import ServedCompetitions
from backend.app.services.fixture_feature_service import resolve_features
from backend.app.services.season_tools import SeasonTools
from backend.app.services.team_resolver import TeamNotFoundError, resolve_team

_EXPECTED_ERRORS = (
    FeatureMissingError,
    FixtureFeaturesNotAvailableError,
    FixturesNotAvailableError,
    ModelNotAvailableError,
    UnknownCompetitionError,
    UnknownTeamError,
    ValidationError,
)
_DEFAULT_FIXTURES = 10
_MAX_FIXTURES = 20


class AssistantTools:
    """Builds the assistant's tools over the services held in ``app.state``."""

    def __init__(self, state: Any, competitions: ServedCompetitions) -> None:
        """Initialise with the app state and the served leagues."""
        self._state = state
        self._competitions = competitions

    def tools(self) -> list[Tool]:
        """Return the prediction, explanation, fixtures and season tools."""
        return [
            *self._api_tools(),
            *SeasonTools(self._state, self._competitions).tools(),
        ]

    def _api_tools(self) -> list[Tool]:
        names = list(self._competitions.names)
        match = _match_parameters(names)
        return [
            Tool(
                "predict_match",
                "Model prediction for a match: predicted result (H/D/A) and the "
                "probability of each outcome. draw_possible flags a likelier "
                "than usual draw; false does not mean a draw cannot happen.",
                match,
                _expected(self.predict_match),
            ),
            Tool(
                "explain_match",
                "SHAP explanation of a match prediction: the features that "
                "pushed the predicted result up and down, with their values.",
                match,
                _expected(self.explain_match),
            ),
            Tool(
                "upcoming_fixtures",
                "A league's next scheduled matches, earliest first. For one team's "
                "fixtures or the next meeting of two teams, use team_matches.",
                _fixtures_parameters(names),
                _expected(self.upcoming_fixtures),
            ),
        ]

    def predict_match(self, args: Mapping[str, Any]) -> dict[str, Any]:
        """Run POST /v2/predict's service for the requested match."""
        service = self._service("prediction_service", "Prediction model")
        request, competition, features = self._resolve(args)
        response = service.predict(request.model_copy(update={"features": features}))
        result: dict[str, Any] = response.model_copy(
            update={"competition": competition}
        ).model_dump(mode="json")
        rounded: dict[str, Any] = _rounded(result)
        return rounded

    def explain_match(self, args: Mapping[str, Any]) -> dict[str, Any]:
        """Run POST /v2/explain's service, keeping the top contributors only."""
        service = self._service("explanation_service", "Explanation service")
        request, competition, features = self._resolve(args)
        response = service.explain(request.home_team, request.away_team, features)
        result: dict[str, Any] = response.model_copy(
            update={"competition": competition}
        ).model_dump(mode="json", exclude={"all_contributions"})
        rounded: dict[str, Any] = _rounded(result)
        return rounded

    def upcoming_fixtures(self, args: Mapping[str, Any]) -> dict[str, Any]:
        """Run GET /v2/fixtures' service for the requested league."""
        service = self._service("fixtures_service", "Fixtures")
        competition = self._competitions.resolve(args.get("competition") or None)
        limit = _limit(args.get("limit"))
        result: dict[str, Any] = service.upcoming(competition, limit).model_dump(
            mode="json"
        )
        return result

    def _service(self, attribute: str, label: str) -> Any:
        service = getattr(self._state, attribute, None)
        if service is None:
            raise ModelNotAvailableError(f"{label} is not loaded on the server.")
        return service

    def _resolve(
        self, args: Mapping[str, Any]
    ) -> tuple[PredictionRequest, str, dict[str, float]]:
        competition = self._competitions.resolve(args.get("competition") or None)
        request = PredictionRequest(
            home_team=self._team_name(args.get("home_team", ""), competition),
            away_team=self._team_name(args.get("away_team", ""), competition),
            competition=competition,
        )
        fixtures = getattr(self._state, "fixture_feature_service", None)
        return request, competition, resolve_features(request, fixtures, competition)

    def _team_name(self, name: str, competition: str) -> str:
        """The data's spelling of ``name``, or ``name`` unchanged if unknown."""
        season = getattr(self._state, "season_service", None)
        if season is None or not name:
            return name
        try:
            return resolve_team(name, season.teams(competition))
        except (TeamNotFoundError, ValueError):
            return name


def _match_parameters(leagues: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "home_team": {"type": "string", "description": "Home team name."},
            "away_team": {"type": "string", "description": "Away team name."},
            "competition": {"type": "string", "enum": leagues},
        },
        "required": ["home_team", "away_team"],
    }


def _fixtures_parameters(leagues: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "competition": {"type": "string", "enum": leagues},
            "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_FIXTURES},
        },
        "required": [],
    }


def _rounded(value: Any) -> Any:
    """Floats to 3 decimals, everywhere in a tool result.

    Small models truncate long floats (0.64996 written as 64.99%) instead of
    rounding them; three decimals still give a percentage to one decimal.
    """
    if isinstance(value, float):
        return round(value, 3)
    if isinstance(value, dict):
        return {key: _rounded(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_rounded(item) for item in value]
    return value


def _limit(value: Any) -> int:
    try:
        requested = int(value or _DEFAULT_FIXTURES)
    except (TypeError, ValueError) as exc:
        raise ToolError(f"limit must be a whole number, not {value!r}.") from exc
    return min(max(requested, 1), _MAX_FIXTURES)


def _expected(handler: ToolHandler) -> ToolHandler:
    """Turn the API's expected errors into a ToolError the model can read."""

    def run(args: Mapping[str, Any]) -> Any:
        try:
            return handler(args)
        except _EXPECTED_ERRORS as exc:
            raise ToolError(str(exc)) from exc

    return run
