"""Rest days features: days since each team's last match."""

from __future__ import annotations

import pandas as pd

from feature_engineering.base import BaseFeature, build_team_match_view


class RestDaysFeature(BaseFeature):
    """Computes days since each team's previous match (home or away)."""

    @property
    def name(self) -> str:
        return "rest_days"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def output_columns(self) -> list[str]:
        return ["home_rest_days", "away_rest_days"]

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute rest days for home and away teams.

        For each match, calculates the number of days since that team's
        immediately preceding match. NaN is returned for a team's first match.
        """
        tv = build_team_match_view(df)
        tv["match_date"] = pd.to_datetime(tv["match_date"])

        tv["days_since_last"] = tv.groupby("team")["match_date"].transform(
            lambda x: x.diff().dt.days
        )

        home_tv = tv[tv["is_home"]].set_index("_original_idx")
        away_tv = tv[~tv["is_home"]].set_index("_original_idx")

        result = pd.DataFrame(index=df.index)
        result["home_rest_days"] = home_tv["days_since_last"].reindex(df.index)
        result["away_rest_days"] = away_tv["days_since_last"].reindex(df.index)

        return result
