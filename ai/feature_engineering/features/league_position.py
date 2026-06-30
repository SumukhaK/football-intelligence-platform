"""League position features: running points table standings before each match."""

from __future__ import annotations

from collections import defaultdict

import pandas as pd

from feature_engineering.base import BaseFeature


class LeaguePositionFeature(BaseFeature):
    """Maintains a running points table and records each team's position per match."""

    @property
    def name(self) -> str:
        return "league_position"

    @property
    def version(self) -> str:
        return "1.0.0"

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

        Records standings BEFORE updating with each match's result, so the
        current match is not included in its own position calculation.
        """
        points_table: dict[str, int] = defaultdict(int)
        played_table: dict[str, int] = defaultdict(int)

        home_positions: list[int | None] = []
        away_positions: list[int | None] = []
        home_points_list: list[int] = []
        away_points_list: list[int] = []
        home_played_list: list[int] = []
        away_played_list: list[int] = []

        for _, row in df.iterrows():
            home = row["home_team"]
            away = row["away_team"]

            # Record position BEFORE this match updates the table
            home_pts = points_table[home]
            away_pts = points_table[away]
            home_played = played_table[home]
            away_played = played_table[away]

            if points_table:
                home_pos = self._position_from_points(home, points_table)
                away_pos = self._position_from_points(away, points_table)
            else:
                home_pos = 1
                away_pos = 1

            home_positions.append(home_pos)
            away_positions.append(away_pos)
            home_points_list.append(home_pts)
            away_points_list.append(away_pts)
            home_played_list.append(home_played)
            away_played_list.append(away_played)

            # Update table with this match's result
            result = row["result"]
            if result == "H":
                points_table[home] += 3
            elif result == "D":
                points_table[home] += 1
                points_table[away] += 1
            else:  # "A"
                points_table[away] += 3

            played_table[home] += 1
            played_table[away] += 1

        return pd.DataFrame(
            {
                "home_league_position": home_positions,
                "away_league_position": away_positions,
                "home_league_points": home_points_list,
                "away_league_points": away_points_list,
                "home_matches_played": home_played_list,
                "away_matches_played": away_played_list,
            },
            index=df.index,
        )
