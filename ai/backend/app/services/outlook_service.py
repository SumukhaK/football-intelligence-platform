"""A team's season outlook: projected finish and how its chances moved (ADR 023).

The current projection uses the goals model ``/insights`` uses. Each history
point is a projection as it stood on its date: the table from matches played
before the cutoff, and a goals model refitted only on those matches.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from backend.app.exceptions import SeasonOutlookNotAvailableError, UnknownTeamError
from backend.app.schemas.outlook import (
    OutlookPointSchema,
    TeamOutlookResponse,
    TeamProjectionSchema,
    TeamStrengthSchema,
)
from backend.app.services.season_service import unplayed
from goals.dixon_coles import DixonColesParams, fit_dixon_coles
from goals.insights import team_strengths
from goals.season_table import DEFAULT_SIMULATIONS, project_table, standings
from inference.fixture_features import find_latest_dataset

# A 30% chance from 2,000 runs carries a standard error of about one point.
HISTORY_SIMULATIONS = 2_000
_COLUMNS = [
    "match_date",
    "season",
    "competition",
    "home_team",
    "away_team",
    "full_time_home_goals",
    "full_time_away_goals",
]
_PAIR = ["home_team", "away_team"]


class OutlookService:
    """Answers GET /teams/{team}/outlook, caching each league's history points."""

    def __init__(
        self,
        matches: pd.DataFrame,
        today: Callable[[], date] = date.today,
        history_simulations: int = HISTORY_SIMULATIONS,
    ) -> None:
        """Initialise with every played match, a clock and the history run count."""
        frame = matches[_COLUMNS].copy()
        frame["match_date"] = pd.to_datetime(frame["match_date"]).dt.date
        self._matches = frame.sort_values("match_date", kind="stable")
        self._today = today
        self._history_simulations = history_simulations
        self._cache: dict[tuple[str, date], pd.DataFrame] = {}
        # ponytail: one lock for every league; per-league locks if requests queue.
        self._lock = threading.Lock()

    @classmethod
    def from_directory(cls, directory: Path) -> OutlookService:
        """Load the newest match dataset in ``directory``."""
        return cls(pd.read_csv(find_latest_dataset(directory)))

    def outlook(
        self,
        team: str,
        competition: str,
        schedule: pd.DataFrame,
        params: DixonColesParams,
        model_version: str,
    ) -> TeamOutlookResponse:
        """The team's projected finish, the projected table and the history.

        Raises:
            SeasonOutlookNotAvailableError: If the league has no match history.
            UnknownTeamError: If the team is not in the league this season.
        """
        league = self._matches[self._matches["competition"] == competition]
        if league.empty:
            raise SeasonOutlookNotAvailableError(f"No match history for {competition}.")
        season = str(league["season"].max())
        this_season = league[league["season"] == season]
        today = self._today()
        current = _project(this_season, schedule, today, params, DEFAULT_SIMULATIONS)
        if team not in current.index:
            raise UnknownTeamError(team, competition, season)
        strengths = team_strengths(params, team, team)
        return TeamOutlookResponse(
            competition=competition,
            season=season,
            team=team,
            as_of=today,
            model_version=model_version,
            fitted_before=params.fitted_before,
            simulations=DEFAULT_SIMULATIONS,
            history_simulations=self._history_simulations,
            projection=_projection(current, team),
            strengths=TeamStrengthSchema(
                attack=strengths.home_attack, defence=strengths.home_defence
            ),
            table=[_projection(current, name) for name in current.index],
            history=self._history(team, league, this_season, schedule, today),
        )

    def _history(
        self,
        team: str,
        league: pd.DataFrame,
        this_season: pd.DataFrame,
        schedule: pd.DataFrame,
        today: date,
    ) -> list[OutlookPointSchema]:
        competition = str(league["competition"].iloc[0])
        points = []
        for cutoff in _cutoffs(this_season, today):
            projection = self._projection_at(
                competition, cutoff, league, this_season, schedule
            )
            if team in projection.index:
                points.append(_point(projection, team, this_season, cutoff))
        return points

    def _projection_at(
        self,
        competition: str,
        cutoff: date,
        league: pd.DataFrame,
        this_season: pd.DataFrame,
        schedule: pd.DataFrame,
    ) -> pd.DataFrame:
        """The league's projection as it stood at ``cutoff``, computed once."""
        with self._lock:
            key = (competition, cutoff)
            if key not in self._cache:
                params = fit_dixon_coles(
                    league, pd.Timestamp(cutoff), competition=competition
                )
                self._cache[key] = _project(
                    this_season, schedule, cutoff, params, self._history_simulations
                )
            return self._cache[key]


def _project(
    this_season: pd.DataFrame,
    schedule: pd.DataFrame,
    cutoff: date,
    params: DixonColesParams,
    simulations: int,
) -> pd.DataFrame:
    """Simulate every match not played before ``cutoff`` onto the table then."""
    played = this_season[this_season["match_date"] < cutoff]
    later = this_season[this_season["match_date"] >= cutoff][_PAIR]
    remaining = pd.concat([later, unplayed(schedule, played_all=this_season)[_PAIR]])
    # Sorted so the same fixtures give the same draws, whichever data they came from.
    remaining = remaining.sort_values(_PAIR, kind="stable").reset_index(drop=True)
    teams = set(played["home_team"]) | set(played["away_team"])
    teams |= set(remaining["home_team"]) | set(remaining["away_team"])
    table = standings(played, teams=sorted(teams))
    return project_table(table, remaining, params, simulations=simulations)


def _cutoffs(this_season: pd.DataFrame, today: date) -> list[date]:
    """The season's first match day, then the Monday after each week with a match.

    Each cutoff is exclusive: a Monday match counts towards the next week.
    Weeks still in progress are left to the current projection.
    """
    days = sorted(set(this_season["match_date"]))
    if not days:
        return []
    mondays = {day + timedelta(days=7 - day.weekday()) for day in days}
    return [days[0], *sorted(m for m in mondays if m <= today)]


def _projection(projection: pd.DataFrame, team: str) -> TeamProjectionSchema:
    row = projection.loc[team].to_dict()
    return TeamProjectionSchema(
        team=team,
        current_points=int(row["current_points"]),
        expected_points=float(row["expected_points"]),
        most_likely_position=int(row["most_likely_position"]),
        chance_first=float(row["chance_first"]),
        chance_top_four=float(row["chance_top_four"]),
        chance_bottom_three=float(row["chance_bottom_three"]),
    )


def _point(
    projection: pd.DataFrame, team: str, this_season: pd.DataFrame, cutoff: date
) -> OutlookPointSchema:
    played = this_season[this_season["match_date"] < cutoff]
    games = int(((played["home_team"] == team) | (played["away_team"] == team)).sum())
    row = projection.loc[team].to_dict()
    return OutlookPointSchema(
        as_of=cutoff - timedelta(days=1),
        played=games,
        most_likely_position=int(row["most_likely_position"]),
        chance_first=float(row["chance_first"]),
        chance_top_four=float(row["chance_top_four"]),
        chance_bottom_three=float(row["chance_bottom_three"]),
    )
