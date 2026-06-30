"""Head-to-head features: historical outcomes between paired teams."""

from __future__ import annotations

import pandas as pd

from feature_engineering.base import BaseFeature


class HeadToHeadFeature(BaseFeature):
    """Computes historical head-to-head record between the home and away team."""

    @property
    def name(self) -> str:
        return "head_to_head"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def output_columns(self) -> list[str]:
        return ["h2h_meetings", "h2h_home_wins", "h2h_away_wins", "h2h_draws"]

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute head-to-head statistics for each match.

        For match i, considers all prior matches (index < i) between
        home_team and away_team in either direction. O(n²) — acceptable
        for typical season-length datasets (~380 rows).
        """
        meetings_list: list[int] = []
        home_wins_list: list[int] = []
        away_wins_list: list[int] = []
        draws_list: list[int] = []

        for i, row in df.iterrows():
            team_a = row["home_team"]
            team_b = row["away_team"]

            prior = df.loc[:i].iloc[:-1]  # all rows before this one

            mask = ((prior["home_team"] == team_a) & (prior["away_team"] == team_b)) | (
                (prior["home_team"] == team_b) & (prior["away_team"] == team_a)
            )
            h2h = prior[mask]

            meetings = len(h2h)

            # Wins for team_a (current home team)
            a_home_wins = int(
                ((h2h["home_team"] == team_a) & (h2h["result"] == "H")).sum()
            )
            a_away_wins = int(
                ((h2h["away_team"] == team_a) & (h2h["result"] == "A")).sum()
            )
            home_wins = a_home_wins + a_away_wins

            # Wins for team_b (current away team)
            b_home_wins = int(
                ((h2h["home_team"] == team_b) & (h2h["result"] == "H")).sum()
            )
            b_away_wins = int(
                ((h2h["away_team"] == team_b) & (h2h["result"] == "A")).sum()
            )
            away_wins = b_home_wins + b_away_wins

            draws = int((h2h["result"] == "D").sum())

            meetings_list.append(meetings)
            home_wins_list.append(home_wins)
            away_wins_list.append(away_wins)
            draws_list.append(draws)

        result = pd.DataFrame(
            {
                "h2h_meetings": meetings_list,
                "h2h_home_wins": home_wins_list,
                "h2h_away_wins": away_wins_list,
                "h2h_draws": draws_list,
            },
            index=df.index,
        )

        return result
