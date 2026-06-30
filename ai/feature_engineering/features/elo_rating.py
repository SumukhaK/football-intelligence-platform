"""Elo rating features: dynamic ratings updated after each completed match."""

from __future__ import annotations

from collections import defaultdict

import pandas as pd

from feature_engineering.base import BaseFeature

_K = 32
_START_ELO = 1500.0


class EloRatingFeature(BaseFeature):
    """Computes dynamic Elo ratings, recording each team's rating before the match."""

    @property
    def name(self) -> str:
        return "elo_rating"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def output_columns(self) -> list[str]:
        return ["home_elo_before", "away_elo_before"]

    def _expected_score(self, rating_a: float, rating_b: float) -> float:
        """Compute expected score for team A against team B."""
        return float(1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0)))

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute Elo ratings iteratively, recording pre-match ratings.

        Teams start at 1500. Ratings are updated after each match using
        the standard Elo formula with K=32.
        """
        elo_table: dict[str, float] = defaultdict(lambda: _START_ELO)

        home_elo_before: list[float] = []
        away_elo_before: list[float] = []

        for _, row in df.iterrows():
            home = row["home_team"]
            away = row["away_team"]

            home_elo = elo_table[home]
            away_elo = elo_table[away]

            home_elo_before.append(home_elo)
            away_elo_before.append(away_elo)

            expected_home = self._expected_score(home_elo, away_elo)
            expected_away = 1.0 - expected_home

            result = row["result"]
            if result == "H":
                actual_home, actual_away = 1.0, 0.0
            elif result == "D":
                actual_home, actual_away = 0.5, 0.5
            else:  # "A"
                actual_home, actual_away = 0.0, 1.0

            elo_table[home] = home_elo + _K * (actual_home - expected_home)
            elo_table[away] = away_elo + _K * (actual_away - expected_away)

        return pd.DataFrame(
            {
                "home_elo_before": home_elo_before,
                "away_elo_before": away_elo_before,
            },
            index=df.index,
        )
