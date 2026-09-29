"""Head-to-head features: historical outcomes between paired teams."""

from __future__ import annotations

from collections import defaultdict

import pandas as pd

from feature_engineering.base import BaseFeature


class HeadToHeadFeature(BaseFeature):
    """Computes historical head-to-head record between the home and away team."""

    @property
    def name(self) -> str:
        return "head_to_head"

    @property
    def version(self) -> str:
        return "1.0.1"

    @property
    def output_columns(self) -> list[str]:
        return ["h2h_meetings", "h2h_home_wins", "h2h_away_wins", "h2h_draws"]

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute head-to-head statistics for each match.

        For match i, counts all prior rows (index < i) between home_team and
        away_team in either direction. Wins are tracked per team for each
        unordered pair, so one pass is enough for multi-season datasets.
        """
        # pair -> [wins for team, wins for other team, draws], keyed by team name
        wins: dict[frozenset[str], dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        draws: dict[frozenset[str], int] = defaultdict(int)
        rows: list[tuple[int, int, int, int]] = []

        for row in df.itertuples(index=False):
            home, away = str(row.home_team), str(row.away_team)
            pair = frozenset((home, away))
            home_wins, away_wins = wins[pair][home], wins[pair][away]
            rows.append(
                (home_wins + away_wins + draws[pair], home_wins, away_wins, draws[pair])
            )
            if row.result == "H":
                wins[pair][home] += 1
            elif row.result == "A":
                wins[pair][away] += 1
            else:
                draws[pair] += 1

        return pd.DataFrame(rows, index=df.index, columns=self.output_columns)
