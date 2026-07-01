"""Home advantage features: each team's historical home win % and points per game."""

from __future__ import annotations

import pandas as pd

from feature_engineering.base import BaseFeature, build_team_match_view


class HomeAdvantageFeature(BaseFeature):
    """Computes historical home performance metrics using an expanding window."""

    @property
    def name(self) -> str:
        return "home_advantage"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def output_columns(self) -> list[str]:
        return ["home_win_pct", "home_ppg"]

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute home win percentage and points per game for the home team.

        Uses an expanding window over prior home games only. shift(1) ensures
        the current match is excluded from the calculation.
        """
        tv = build_team_match_view(df)
        home_only = tv[tv["is_home"]].copy()

        def _expanding_mean(series: pd.Series) -> pd.Series:
            return series.shift(1).expanding(min_periods=1).mean()

        home_only["win_pct"] = home_only.groupby("team")["win"].transform(
            _expanding_mean
        )
        home_only["ppg"] = home_only.groupby("team")["points"].transform(
            _expanding_mean
        )

        home_indexed = home_only.set_index("_original_idx")

        result = pd.DataFrame(index=df.index)
        result["home_win_pct"] = home_indexed["win_pct"].reindex(df.index)
        result["home_ppg"] = home_indexed["ppg"].reindex(df.index)

        # Fill NaN for teams with no prior home history with 0.0
        result["home_win_pct"] = result["home_win_pct"].fillna(0.0)
        result["home_ppg"] = result["home_ppg"].fillna(0.0)

        return result
