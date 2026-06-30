"""Goal statistics features: rolling mean goals scored, conceded, and differential."""

from __future__ import annotations

import pandas as pd

from feature_engineering.base import BaseFeature, build_team_match_view


class GoalStatisticsFeature(BaseFeature):
    """Computes rolling average goals scored and conceded over last 5 and 10 matches."""

    @property
    def name(self) -> str:
        return "goal_statistics"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def output_columns(self) -> list[str]:
        return [
            "home_goals_scored_last5",
            "home_goals_scored_last10",
            "home_goals_conceded_last5",
            "home_goals_conceded_last10",
            "home_goal_diff_last5",
            "home_goal_diff_last10",
            "away_goals_scored_last5",
            "away_goals_scored_last10",
            "away_goals_conceded_last5",
            "away_goals_conceded_last10",
            "away_goal_diff_last5",
            "away_goal_diff_last10",
        ]

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute rolling goal statistics using team-match view.

        Uses shift(1) before rolling to prevent data leakage from the
        current match's goals.
        """
        tv = build_team_match_view(df)

        def _rolling_mean(series: pd.Series, window: int) -> pd.Series:
            return series.shift(1).rolling(window, min_periods=1).mean()

        tv["scored_last5"] = tv.groupby("team")["goals_scored"].transform(
            lambda s: _rolling_mean(s, 5)
        )
        tv["scored_last10"] = tv.groupby("team")["goals_scored"].transform(
            lambda s: _rolling_mean(s, 10)
        )
        tv["conceded_last5"] = tv.groupby("team")["goals_conceded"].transform(
            lambda s: _rolling_mean(s, 5)
        )
        tv["conceded_last10"] = tv.groupby("team")["goals_conceded"].transform(
            lambda s: _rolling_mean(s, 10)
        )
        tv["goal_diff_last5"] = tv["scored_last5"] - tv["conceded_last5"]
        tv["goal_diff_last10"] = tv["scored_last10"] - tv["conceded_last10"]

        home_tv = tv[tv["is_home"]].set_index("_original_idx")
        away_tv = tv[~tv["is_home"]].set_index("_original_idx")

        result = pd.DataFrame(index=df.index)
        result["home_goals_scored_last5"] = home_tv["scored_last5"]
        result["home_goals_scored_last10"] = home_tv["scored_last10"]
        result["home_goals_conceded_last5"] = home_tv["conceded_last5"]
        result["home_goals_conceded_last10"] = home_tv["conceded_last10"]
        result["home_goal_diff_last5"] = home_tv["goal_diff_last5"]
        result["home_goal_diff_last10"] = home_tv["goal_diff_last10"]
        result["away_goals_scored_last5"] = away_tv["scored_last5"]
        result["away_goals_scored_last10"] = away_tv["scored_last10"]
        result["away_goals_conceded_last5"] = away_tv["conceded_last5"]
        result["away_goals_conceded_last10"] = away_tv["conceded_last10"]
        result["away_goal_diff_last5"] = away_tv["goal_diff_last5"]
        result["away_goal_diff_last10"] = away_tv["goal_diff_last10"]

        return result
