"""Rolling form features: recent wins and points over last 5 and 10 matches."""

from __future__ import annotations

import pandas as pd

from feature_engineering.base import BaseFeature, build_team_match_view


class RollingFormFeature(BaseFeature):
    """Computes rolling win counts and points totals for each team."""

    @property
    def name(self) -> str:
        return "rolling_form"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def output_columns(self) -> list[str]:
        return [
            "home_form_wins_last5",
            "home_form_wins_last10",
            "home_form_points_last5",
            "home_form_points_last10",
            "away_form_wins_last5",
            "away_form_wins_last10",
            "away_form_points_last5",
            "away_form_points_last10",
        ]

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute rolling form features using team-match view.

        Uses shift(1) before rolling to prevent data leakage from the
        current match's result.
        """
        tv = build_team_match_view(df)

        def _rolling_sum(series: pd.Series, window: int) -> pd.Series:
            return series.shift(1).rolling(window, min_periods=1).sum()

        tv["wins_last5"] = tv.groupby("team")["win"].transform(
            lambda s: _rolling_sum(s, 5)
        )
        tv["wins_last10"] = tv.groupby("team")["win"].transform(
            lambda s: _rolling_sum(s, 10)
        )
        tv["points_last5"] = tv.groupby("team")["points"].transform(
            lambda s: _rolling_sum(s, 5)
        )
        tv["points_last10"] = tv.groupby("team")["points"].transform(
            lambda s: _rolling_sum(s, 10)
        )

        home_tv = tv[tv["is_home"]].set_index("_original_idx")
        away_tv = tv[~tv["is_home"]].set_index("_original_idx")

        result = pd.DataFrame(index=df.index)
        result["home_form_wins_last5"] = home_tv["wins_last5"]
        result["home_form_wins_last10"] = home_tv["wins_last10"]
        result["home_form_points_last5"] = home_tv["points_last5"]
        result["home_form_points_last10"] = home_tv["points_last10"]
        result["away_form_wins_last5"] = away_tv["wins_last5"]
        result["away_form_wins_last10"] = away_tv["wins_last10"]
        result["away_form_points_last5"] = away_tv["points_last5"]
        result["away_form_points_last10"] = away_tv["points_last10"]

        return result
