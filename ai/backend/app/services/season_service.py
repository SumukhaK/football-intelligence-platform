"""Season questions for the assistant: results, meetings and tables (ADR 021).

Backs the assistant's internal ``team_matches`` and ``league_table`` tools.
Played matches come from the match history, the rest of the season from the
fixtures dataset, and projections from each league's goals model.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any, cast

import pandas as pd

from goals.dixon_coles import DixonColesParams
from goals.season_table import project_table, standings
from inference.fixture_features import find_latest_dataset, season_for_date

_SEASON = re.compile(r"^\s*(\d{4})\s*[/-]\s*(\d{2}|\d{4})\s*$")
_MATCH_COLUMNS = [
    "match_date",
    "season",
    "competition",
    "home_team",
    "away_team",
    "full_time_home_goals",
    "full_time_away_goals",
]


class SeasonQueryError(ValueError):
    """A season question the data cannot answer, worded for the user."""


class SeasonService:
    """Answers season questions from the match history and fixtures."""

    def __init__(
        self, matches: pd.DataFrame, today: Callable[[], date] = date.today
    ) -> None:
        """Initialise with every played match and a clock."""
        frame = matches[_MATCH_COLUMNS].copy()
        frame["match_date"] = pd.to_datetime(frame["match_date"]).dt.date
        self._matches = frame.sort_values("match_date", kind="stable")
        self._today = today

    @classmethod
    def from_directory(cls, directory: Path) -> SeasonService:
        """Load the newest match dataset in ``directory``."""
        return cls(pd.read_csv(find_latest_dataset(directory)))

    def current_season(self, competition: str) -> str:
        """The latest season in the league's history."""
        seasons = self._league(competition)["season"]
        if seasons.empty:
            raise SeasonQueryError(f"No match history for {competition}.")
        return str(seasons.max())

    def teams(self, competition: str, season: str | None = None) -> list[str]:
        """Teams with a result in the league's season (default: current)."""
        season = season or self.current_season(competition)
        played = self._league(competition)
        played = played[played["season"] == season]
        return sorted(set(played["home_team"]) | set(played["away_team"]))

    def league_teams(self, competition: str) -> list[str]:
        """Every team that has played in the league in any season."""
        played = self._league(competition)
        return sorted(set(played["home_team"]) | set(played["away_team"]))

    def team_matches(
        self,
        team: str,
        competition: str,
        schedule: pd.DataFrame,
        opponent: str | None = None,
        season: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """A team's latest results and, this season, its next fixtures.

        With ``opponent``, only meetings between the two teams are listed.
        """
        current = self.current_season(competition)
        season = normalise_season(season) if season else current
        self._check_season(season, current)
        played = self._season_matches(competition, season)
        played = played[_involves(played, team, opponent)]
        result: dict[str, Any] = {
            "competition": competition,
            "season": season,
            "team": team,
            "opponent": opponent,
            "results": [_result(row) for row in _latest(played, limit)],
        }
        if season == current:
            remaining = unplayed(schedule, played_all=played)
            remaining = remaining[_involves(remaining, team, opponent)]
            result["upcoming"] = [_fixture(r) for r in _first(remaining, limit)]
            if opponent and not result["upcoming"]:
                result["note"] = "No more meetings between these teams this season."
        return result

    def league_table(
        self,
        competition: str,
        schedule: pd.DataFrame,
        params: DixonColesParams | None,
        season: str | None = None,
        on: date | None = None,
    ) -> dict[str, Any]:
        """The league table on a date: actual when played, projected if ahead.

        Raises:
            SeasonQueryError: For a future season, or a projection without a
                goals model.
        """
        current = self.current_season(competition)
        season = normalise_season(season) if season else None
        season = season or (season_for_date(on) if on else current)
        self._check_season(season, current)
        played = self._season_matches(competition, season)
        if on is not None:
            played = played[played["match_date"] <= on]
        last_played = played["match_date"].max() if not played.empty else None
        if on is None or season != current or on <= self._today():
            return _actual(competition, season, on or last_played, played)
        if params is None:
            raise SeasonQueryError(f"No goals model to project {competition}.")
        remaining = unplayed(schedule, played_all=played)
        remaining = remaining[remaining["match_date"] <= on.isoformat()]
        return _projected(competition, season, on, played, remaining, params)

    def _league(self, competition: str) -> pd.DataFrame:
        return self._matches[self._matches["competition"] == competition]

    def _season_matches(self, competition: str, season: str) -> pd.DataFrame:
        league = self._league(competition)
        return league[league["season"] == season]

    @staticmethod
    def _check_season(season: str, current: str) -> None:
        if season > current:
            raise SeasonQueryError(
                f"Season {season} has not started; the latest is {current}."
            )


def normalise_season(value: str) -> str:
    """Turn "2026-27", "2026/2027" or "2026/27" into "2026/27".

    Raises:
        SeasonQueryError: If ``value`` is not a season.
    """
    match = _SEASON.match(value)
    if match is None or int(match.group(2)[-2:]) != (int(match.group(1)) + 1) % 100:
        raise SeasonQueryError(f"'{value}' is not a season like 2026/27.")
    start = int(match.group(1))
    return f"{start}/{(start + 1) % 100:02d}"


def _involves(frame: pd.DataFrame, team: str, opponent: str | None) -> pd.Series:
    home, away = frame["home_team"], frame["away_team"]
    mask = (home == team) | (away == team)
    if opponent:
        mask &= (home == opponent) | (away == opponent)
    return mask


def unplayed(schedule: pd.DataFrame, played_all: pd.DataFrame) -> pd.DataFrame:
    """Scheduled matches not yet in the results (each pairing is played once)."""
    done = set(zip(played_all["home_team"], played_all["away_team"], strict=True))
    pairs = zip(schedule["home_team"], schedule["away_team"], strict=True)
    keep = [pair not in done for pair in pairs]
    return schedule[pd.Series(keep, index=schedule.index, dtype=bool)]


def _latest(frame: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], frame.iloc[::-1].head(limit).to_dict("records"))


def _first(frame: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], frame.head(limit).to_dict("records"))


def _result(row: dict[str, Any]) -> dict[str, Any]:
    home, away = int(row["full_time_home_goals"]), int(row["full_time_away_goals"])
    winner = row["home_team"] if home > away else row["away_team"]
    return {
        "date": str(row["match_date"]),
        "home_team": row["home_team"],
        "away_team": row["away_team"],
        "score": f"{home}-{away}",
        "winner": winner if home != away else "draw",
    }


def _fixture(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": row["match_date"],
        "kickoff": row["kickoff"] or None,
        "home_team": row["home_team"],
        "away_team": row["away_team"],
        "round": row["round"],
    }


def _actual(
    competition: str, season: str, on: date | None, played: pd.DataFrame
) -> dict[str, Any]:
    table = standings(played)
    return {
        "competition": competition,
        "season": season,
        "kind": "actual",
        "as_of": str(on) if on else None,
        "leaders": _leaders(
            table,
            {
                "top": "points",
                "most_goals": "goals_for",
                "most_clean_sheets": "clean_sheets",
            },
        ),
        "table": _records(table.reset_index()),
    }


def _projected(
    competition: str,
    season: str,
    on: date,
    played: pd.DataFrame,
    remaining: pd.DataFrame,
    params: DixonColesParams,
) -> dict[str, Any]:
    teams = set(remaining["home_team"]) | set(remaining["away_team"])
    table = standings(played, teams=sorted(teams))
    projection = project_table(table, remaining, params)
    return {
        "competition": competition,
        "season": season,
        "kind": "projection",
        "as_of": str(on),
        "fixtures_simulated": len(remaining),
        "method": "Each remaining fixture simulated 10,000 times with the goals model.",
        # Small models misread long tables, so the answers to the common
        # questions are spelled out.
        "leaders": _leaders(
            projection,
            {
                "most_likely_first": "chance_first",
                "most_likely_most_goals": "chance_most_goals",
                "most_likely_most_clean_sheets": "chance_most_clean_sheets",
            },
        ),
        "table": _records(projection.reset_index(names="team")),
    }


def _leaders(table: pd.DataFrame, columns: dict[str, str]) -> dict[str, Any]:
    """The team leading each column, with its value; empty for an empty table."""
    if table.empty:
        return {}
    return {
        label: {"team": str(table[column].idxmax()), column: table[column].max().item()}
        for label, column in columns.items()
    }


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Rows as plain JSON values (numpy numbers are not JSON-serialisable)."""
    rows: list[dict[str, Any]] = json.loads(frame.to_json(orient="records"))
    return rows
