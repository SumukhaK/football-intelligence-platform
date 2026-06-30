"""Strength of schedule features: rolling average opponent Elo rating."""

from __future__ import annotations

import pandas as pd

from feature_engineering.base import BaseFeature, build_team_match_view


class StrengthOfScheduleFeature(BaseFeature):
    """Computes rolling average opponent Elo over the last 5 and 10 matches."""

    @property
    def name(self) -> str:
        return "strength_of_schedule"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        return ["elo_rating"]

    @property
    def output_columns(self) -> list[str]:
        return [
            "home_avg_opp_elo_last5",
            "home_avg_opp_elo_last10",
            "away_avg_opp_elo_last5",
            "away_avg_opp_elo_last10",
        ]

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute rolling average opponent Elo using pre-match ratings.

        Requires ``home_elo_before`` and ``away_elo_before`` to already be
        present in ``df`` (provided by the ``elo_rating`` feature).
        """
        tv = build_team_match_view(df)

        # Map elo values from df using _original_idx
        tv["home_elo"] = tv["_original_idx"].map(df["home_elo_before"])
        tv["away_elo"] = tv["_original_idx"].map(df["away_elo_before"])

        # If team was home: opponent_elo = away_elo; if away: opponent_elo = home_elo
        tv["opponent_elo_before"] = tv["away_elo"].where(tv["is_home"], tv["home_elo"])

        def _rolling_mean(series: pd.Series, window: int) -> pd.Series:
            return series.shift(1).rolling(window, min_periods=1).mean()

        tv["opp_elo_last5"] = tv.groupby("team")["opponent_elo_before"].transform(
            lambda s: _rolling_mean(s, 5)
        )
        tv["opp_elo_last10"] = tv.groupby("team")["opponent_elo_before"].transform(
            lambda s: _rolling_mean(s, 10)
        )

        home_tv = tv[tv["is_home"]].set_index("_original_idx")
        away_tv = tv[~tv["is_home"]].set_index("_original_idx")

        result = pd.DataFrame(index=df.index)
        result["home_avg_opp_elo_last5"] = home_tv["opp_elo_last5"].reindex(df.index)
        result["home_avg_opp_elo_last10"] = home_tv["opp_elo_last10"].reindex(df.index)
        result["away_avg_opp_elo_last5"] = away_tv["opp_elo_last5"].reindex(df.index)
        result["away_avg_opp_elo_last10"] = away_tv["opp_elo_last10"].reindex(df.index)

        return result
