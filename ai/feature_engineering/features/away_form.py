"""Away form features: each team's historical away win % and points per game."""

from __future__ import annotations

import pandas as pd

from feature_engineering.base import BaseFeature, build_team_match_view


class AwayFormFeature(BaseFeature):
    """Computes historical away performance metrics using an expanding window."""

    @property
    def name(self) -> str:
        return "away_form"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def output_columns(self) -> list[str]:
        return ["away_win_pct", "away_ppg"]

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute away win percentage and points per game for the away team.

        Uses an expanding window over prior away games only. shift(1) ensures
        the current match is excluded from the calculation.
        """
        tv = build_team_match_view(df)
        away_only = tv[~tv["is_home"]].copy()

        def _expanding_mean(series: pd.Series) -> pd.Series:
            return series.shift(1).expanding(min_periods=1).mean()

        away_only["win_pct"] = away_only.groupby("team")["win"].transform(
            _expanding_mean
        )
        away_only["ppg"] = away_only.groupby("team")["points"].transform(
            _expanding_mean
        )

        away_indexed = away_only.set_index("_original_idx")

        result = pd.DataFrame(index=df.index)
        result["away_win_pct"] = away_indexed["win_pct"].reindex(df.index)
        result["away_ppg"] = away_indexed["ppg"].reindex(df.index)

        # Fill NaN for teams with no prior away history with 0.0
        result["away_win_pct"] = result["away_win_pct"].fillna(0.0)
        result["away_ppg"] = result["away_ppg"].fillna(0.0)

        return result
