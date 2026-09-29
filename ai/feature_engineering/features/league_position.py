"""League position features: running points table standings before each match.

Each (competition, season) keeps its own table, so standings reset every season
and leagues never share a table. Standings are taken at the start of each
match date, so simultaneous kick-offs never see each other's results.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd

from feature_engineering.base import BaseFeature


class LeaguePositionFeature(BaseFeature):
    """Maintains a running points table and records each team's position per match."""

    @property
    def name(self) -> str:
        return "league_position"

    @property
    def version(self) -> str:
        return "1.1.0"

    @property
    def output_columns(self) -> list[str]:
        return [
            "home_league_position",
            "away_league_position",
            "home_league_points",
            "away_league_points",
            "home_matches_played",
            "away_matches_played",
        ]

    def _position_from_points(self, team: str, points_table: dict[str, int]) -> int:
        """Compute 1-based league position for ``team`` given the current table.

        Tie-breaking is by points only: position = count of teams with strictly
        more points + 1.
        """
        team_pts = points_table[team]
        ahead = sum(1 for pts in points_table.values() if pts > team_pts)
        return ahead + 1

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute league standing features using an iterative points table.

        Standings are snapshotted at the start of each match date: every match
        on a date sees the table before any of that day's results, so the
        output does not depend on the order of same-day rows.
        """
        tables = _Tables()
        records: dict[object, tuple[int, int, int, int, int, int]] = {}
        pending: list[Any] = []
        current_date: object = None

        ordered = df.sort_values("match_date", kind="stable")
        for idx, row in zip(
            ordered.index, ordered.itertuples(index=False), strict=True
        ):
            if row.match_date != current_date:
                for done in pending:
                    tables.apply(done)
                pending, current_date = [], row.match_date
            records[idx] = self._standings(row, tables)
            pending.append(row)

        return pd.DataFrame(
            [records[idx] for idx in df.index],
            index=df.index,
            columns=self.output_columns,
        )

    def _standings(
        self, row: Any, tables: _Tables
    ) -> tuple[int, int, int, int, int, int]:
        """Return both teams' position, points and games played before ``row``."""
        points, played = tables.for_row(row)
        home, away = str(row.home_team), str(row.away_team)
        home_pts, away_pts = points[home], points[away]
        return (
            self._position_from_points(home, points),
            self._position_from_points(away, points),
            home_pts,
            away_pts,
            played[home],
            played[away],
        )


class _Tables:
    """Points and games-played tables, one per (competition, season)."""

    def __init__(self) -> None:
        self._points: dict[tuple[str, str], dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._played: dict[tuple[str, str], dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

    def for_row(self, row: Any) -> tuple[dict[str, int], dict[str, int]]:
        """Return the points and played tables for a row's competition season."""
        key = (str(row.competition), str(row.season))
        return self._points[key], self._played[key]

    def apply(self, row: Any) -> None:
        """Add a finished match to its competition season's tables."""
        _apply_result(*self.for_row(row), row)


def _apply_result(points: dict[str, int], played: dict[str, int], row: Any) -> None:
    """Add one match's points and appearances to a league table."""
    home, away = str(row.home_team), str(row.away_team)
    if row.result == "H":
        points[home] += 3
    elif row.result == "D":
        points[home] += 1
        points[away] += 1
    else:  # "A"
        points[away] += 3
    played[home] += 1
    played[away] += 1
