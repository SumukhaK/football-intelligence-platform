"""Internal assistant tools for season questions (ADR 021).

``team_matches`` answers results, head-to-head and "when do they meet next"
questions; ``league_table`` answers standings on any date of a season we
hold, projecting the table when the date is still ahead. They are not API
endpoints: only the assistant calls them.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any

import pandas as pd

from assistant.tools.tool import Tool, ToolError, ToolHandler
from backend.app.exceptions import UnknownCompetitionError
from backend.app.services.competitions import ServedCompetitions
from backend.app.services.season_service import (
    SeasonQueryError,
    SeasonService,
    normalise_season,
)
from backend.app.services.team_resolver import TeamNotFoundError, resolve_team

_DEFAULT_RESULTS = 5
_MAX_RESULTS = 20


class SeasonTools:
    """Builds the season tools over the services held in ``app.state``."""

    def __init__(self, state: Any, competitions: ServedCompetitions) -> None:
        """Initialise with the app state and the served leagues."""
        self._state = state
        self._competitions = competitions

    def tools(self) -> list[Tool]:
        """Return the ``team_matches`` and ``league_table`` tools."""
        leagues = list(self._competitions.names)
        return [
            Tool(
                "team_matches",
                "A team's results and remaining fixtures. Use for recent form, "
                "results in a past season, head-to-head meetings, and when two "
                "teams meet next this season (for example the next derby). With "
                "an opponent, lists only their meetings; a note says when no "
                "meeting is left this season.",
                _team_parameters(leagues),
                _season_errors(self.team_matches),
            ),
            Tool(
                "league_table",
                "League standings on a date. For a past date or season it is the "
                "real table. For a date later this season it is a projection: "
                "expected points, goals and clean sheets, and the chance of "
                "finishing first, top four or bottom three, scoring the most "
                "goals or keeping the most clean sheets. Use it for questions "
                "like: who won the league in 2015/16 (season), who will top the "
                "league after Boxing Day (date), who will win the league or "
                "score the most goals this season (date 'end'). Seasons after "
                "the current one are not available.",
                _table_parameters(leagues),
                _season_errors(self.league_table),
            ),
        ]

    def team_matches(self, args: Mapping[str, Any]) -> dict[str, Any]:
        """Results and remaining meetings for the requested team."""
        service = self._season_service()
        competition = self._competition(args, service)
        known = service.league_teams(competition)
        team = resolve_team(str(args.get("team", "")), known)
        opponent = args.get("opponent") or None
        if opponent:
            opponent = resolve_team(str(opponent), known)
        return service.team_matches(
            team,
            competition,
            self._schedule(competition),
            opponent=opponent,
            season=args.get("season") or None,
            limit=_limit(args.get("limit")),
        )

    def league_table(self, args: Mapping[str, Any]) -> dict[str, Any]:
        """The requested league's table, actual or projected."""
        service = self._season_service()
        competition = self._competitions.resolve(args.get("competition") or None)
        insights = getattr(self._state, "insights_service", None)
        season = args.get("season") or None
        on = _date(args.get("date"))
        if str(args.get("date", "")).strip().lower() == "end":
            on = _season_end(season or service.current_season(competition))
        return service.league_table(
            competition,
            self._schedule(competition),
            insights.params(competition) if insights else None,
            season=season,
            on=on,
        )

    def _season_service(self) -> SeasonService:
        service: SeasonService | None = getattr(self._state, "season_service", None)
        if service is None:
            raise ToolError("Match history is not loaded on the server.")
        return service

    def _schedule(self, competition: str) -> pd.DataFrame:
        fixtures = getattr(self._state, "fixtures_service", None)
        if fixtures is None:
            return pd.DataFrame(
                columns=["match_date", "kickoff", "home_team", "away_team", "round"]
            )
        schedule: pd.DataFrame = fixtures.schedule(competition)
        return schedule

    def _competition(self, args: Mapping[str, Any], service: SeasonService) -> str:
        """The named league, else the served league the team plays in now."""
        if args.get("competition"):
            return self._competitions.resolve(str(args["competition"]))
        for league in self._competitions.names:
            try:
                resolve_team(str(args.get("team", "")), service.teams(league))
            except (TeamNotFoundError, SeasonQueryError):
                continue
            return league
        return self._competitions.default


def _team_parameters(leagues: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "team": {"type": "string", "description": "Team name."},
            "opponent": {"type": "string", "description": "Optional opponent."},
            "competition": {"type": "string", "enum": leagues},
            "season": {"type": "string", "description": "Like 2025/26."},
            "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_RESULTS},
        },
        "required": ["team"],
    }


def _table_parameters(leagues: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "competition": {"type": "string", "enum": leagues},
            "season": {"type": "string", "description": "Like 2025/26."},
            "date": {
                "type": "string",
                "description": "YYYY-MM-DD, or 'end' for the end of the season.",
            },
        },
        "required": [],
    }


def _season_end(season: str) -> date:
    """30 June of a season's second year, after its last match."""
    return date(int(normalise_season(season)[:4]) + 1, 6, 30)


def _date(value: Any) -> date | None:
    if not value or str(value).strip().lower() == "end":
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ToolError(f"date must be YYYY-MM-DD, not {value!r}.") from exc


def _limit(value: Any) -> int:
    try:
        requested = int(value or _DEFAULT_RESULTS)
    except (TypeError, ValueError) as exc:
        raise ToolError(f"limit must be a whole number, not {value!r}.") from exc
    return min(max(requested, 1), _MAX_RESULTS)


def _season_errors(handler: ToolHandler) -> ToolHandler:
    """Report season and team-name problems to the model as ToolErrors."""

    def run(args: Mapping[str, Any]) -> Any:
        try:
            return handler(args)
        except (SeasonQueryError, TeamNotFoundError, UnknownCompetitionError) as exc:
            raise ToolError(str(exc)) from exc

    return run
