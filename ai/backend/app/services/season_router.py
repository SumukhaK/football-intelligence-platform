"""Rule-based router for season questions (ADR 021).

Reads the question before the chat model does. Questions about players or
seasons that have not started get a fixed reply with no model call. Table,
results and head-to-head questions get their tool calls decided here, so a
small model only has to write the answer. Anything else goes to the model.
"""

from __future__ import annotations

import calendar
import re
from collections.abc import Callable
from datetime import date
from typing import Any

from assistant.generation.generator import ToolCall
from assistant.tools.routing import Route
from backend.app.services.competitions import ServedCompetitions
from backend.app.services.season_service import (
    SeasonQueryError,
    SeasonService,
    normalise_season,
)
from backend.app.services.team_resolver import aliases, normalise

PLAYER_REPLY = (
    "I can't answer questions about individual players, such as top scorers "
    "or assists: the platform's data covers team results only."
)
FUTURE_SEASON_REPLY = (
    "I can only answer about the current season ({current}) and earlier ones; "
    "{season} hasn't started yet."
)

_LEAGUES = {
    "premier league": "Premier League",
    "epl": "Premier League",
    "prem": "Premier League",
    "bundesliga": "Bundesliga",
    "la liga": "La Liga",
    "laliga": "La Liga",
    "serie a": "Serie A",
    "ligue 1": "Ligue 1",
}
_DERBIES = {
    "manchester derby": ("Man City", "Man United"),
    "north london derby": ("Arsenal", "Tottenham"),
    "merseyside derby": ("Liverpool", "Everton"),
    "el clasico": ("Real Madrid", "Barcelona"),
    "madrid derby": ("Real Madrid", "Ath Madrid"),
    "milan derby": ("Inter", "Milan"),
    "derby della madonnina": ("Inter", "Milan"),
    "der klassiker": ("Bayern Munich", "Dortmund"),
    "le classique": ("Paris SG", "Marseille"),
}
_PLAYER = re.compile(
    r"\b(top ?scorers?|golden boot|assists?|players?|hat ?tricks?|goalscorers?)\b"
)
_NEXT_SEASON = re.compile(r"\bnext season\b")
# Questions are normalised first: punctuation becomes spaces ("2015/16" is
# "2015 16") and "the" is dropped ("win the league" is "win league").
_SEASON = re.compile(r"\b(\d{4}) (\d{2}|\d{4})\b")
_TABLE = re.compile(
    r"\b(table|standings|tops?|win league|won league|title|champions?|"
    r"relegat\w*|bottom|finish\w*|positions?|most goals|clean sheets?|points)\b"
)
_WIN = re.compile(r"\b(wins?|won|winners?)\b")
_SEASON_END = re.compile(
    r"\b(this season|end of season|wins?|won|winners?|title|champions?|"
    r"relegat\w*|finish\w*|most goals|clean sheets?)\b"
)
_RESULTS = re.compile(r"\b(results?|form|last|recent|did|next (game|match|fixture))\b")
_PREDICT = re.compile(r"\b(win|wins|winner|beat|predict\w*|chances?|odds)\b")
_MONTHS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
_HOLIDAYS = {
    "boxing day": (12, 27),  # "after Boxing Day": the table once its games are in
    "christmas": (12, 25),
    "new year": (12, 31),
    "valentine": (2, 14),
    "halloween": (10, 31),
}


class SeasonRouter:
    """Routes season questions using the served leagues' teams."""

    def __init__(
        self,
        state: Any,
        competitions: ServedCompetitions,
        today: Callable[[], date] = date.today,
    ) -> None:
        """Initialise with the app state, the served leagues and a clock."""
        self._state = state
        self._competitions = competitions
        self._today = today

    def route(self, question: str) -> Route | None:
        """Return a fixed reply, tool calls to run first, or None."""
        service: SeasonService | None = getattr(self._state, "season_service", None)
        if service is None:
            return None
        text = normalise(question)
        if _PLAYER.search(text):
            return Route(reply=PLAYER_REPLY)
        teams = self._teams(text, service)
        league = _league(text) or (teams[0][1] if teams else None)
        current = service.current_season(league or self._competitions.default)
        season = _season(text, current)
        if season is not None and season > current:
            return Route(
                reply=FUTURE_SEASON_REPLY.format(current=current, season=season)
            )
        if len(teams) >= 2:
            (team, team_league), (opponent, _) = teams[0], teams[1]
            return self._matches(text, service, team, team_league, opponent, season)
        named_league = _league(text) is not None
        if league and (_TABLE.search(text) or (named_league and _WIN.search(text))):
            return Route(calls=[_table_call(text, league, season, current)])
        if len(teams) == 1 and (_RESULTS.search(text) or _PREDICT.search(text)):
            team, team_league = teams[0]
            return self._matches(text, service, team, team_league, None, season)
        return None

    def _teams(self, text: str, service: SeasonService) -> list[tuple[str, str]]:
        """Teams named in ``text`` with their league, in order of appearance."""
        for name, pair in _DERBIES.items():
            if name in text:
                league = self._league_of(pair[0], service)
                return [(pair[0], league), (pair[1], league)]
        found: list[tuple[int, str, str]] = []
        taken: set[int] = set()
        padded = f" {text} "
        for key, team, league in self._index(service):
            start = padded.find(f" {key} ")
            span = set(range(start, start + len(key)))
            if start >= 0 and not span & taken:
                found.append((start, team, league))
                taken |= span
        return [(team, league) for _, team, league in sorted(found)]

    def _index(self, service: SeasonService) -> list[tuple[str, str, str]]:
        """Every spelling of every served team, longest first."""
        index = []
        for league in self._competitions.names:
            try:
                known = service.league_teams(league)
            except SeasonQueryError:
                continue
            index += [(key, team, league) for key, team in aliases(known).items()]
        return sorted(index, key=lambda entry: -len(entry[0]))

    def _league_of(self, team: str, service: SeasonService) -> str:
        for league in self._competitions.names:
            if team in service.teams(league):
                return league
        return self._competitions.default

    def _matches(
        self,
        text: str,
        service: SeasonService,
        team: str,
        league: str,
        opponent: str | None,
        season: str | None,
    ) -> Route:
        """Results and fixtures, plus a prediction of the next match when asked."""
        calls = [_matches_call(team, league, opponent, season)]
        fixtures = getattr(self._state, "fixtures_service", None)
        if season is None and fixtures is not None and _PREDICT.search(text):
            schedule = fixtures.schedule(league)
            upcoming = service.team_matches(team, league, schedule, opponent)
            nxt = (upcoming.get("upcoming") or [None])[0]
            if nxt is not None:
                calls.append(_predict_call(nxt["home_team"], nxt["away_team"], league))
        return Route(calls=calls)


def _league(text: str) -> str | None:
    for name, league in _LEAGUES.items():
        if re.search(rf"\b{re.escape(name)}\b", text):
            return league
    return None


def _season(text: str, current: str) -> str | None:
    """A season named in the question; "next season" is the one after ``current``."""
    if _NEXT_SEASON.search(text):
        start = int(current[:4]) + 1
        return f"{start}/{(start + 1) % 100:02d}"
    match = _SEASON.search(text)
    if match is None:
        return None
    try:
        return normalise_season(f"{match.group(1)}/{match.group(2)}")
    except SeasonQueryError:
        return None


def _date(text: str, current: str) -> str | None:
    """A date in the current season named in the question, as YYYY-MM-DD."""
    start = int(current[:4])
    for name, (month, day) in _HOLIDAYS.items():
        if name in text:
            return date(start if month >= 7 else start + 1, month, day).isoformat()
    for name, month in _MONTHS.items():
        match = re.search(
            rf"\b(?:(\d{{1,2}}) {name}|{name} (\d{{1,2}})|end of {name})\b", text
        )
        if match:
            year = start if month >= 7 else start + 1
            day_text = match.group(1) or match.group(2)
            last = calendar.monthrange(year, month)[1]
            chosen = min(int(day_text), last) if day_text else last
            return date(year, month, chosen).isoformat()
    return None


def _table_call(text: str, league: str, season: str | None, current: str) -> ToolCall:
    args: dict[str, Any] = {"competition": league}
    if season is not None and season != current:
        args["season"] = season
        return ToolCall("league_table", args)
    when = _date(text, current)
    if when is None and _SEASON_END.search(text):
        when = "end"
    if when is not None:
        args["date"] = when
    return ToolCall("league_table", args)


def _matches_call(
    team: str, league: str, opponent: str | None, season: str | None
) -> ToolCall:
    args: dict[str, Any] = {"team": team, "competition": league}
    if opponent:
        args["opponent"] = opponent
    if season:
        args["season"] = season
    return ToolCall("team_matches", args)


def _predict_call(home: str, away: str, league: str) -> ToolCall:
    return ToolCall(
        "predict_match", {"home_team": home, "away_team": away, "competition": league}
    )
