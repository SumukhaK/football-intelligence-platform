"""Abstract base and shared helper for all feature modules."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


def build_team_match_view(df: pd.DataFrame) -> pd.DataFrame:
    """Create one row per (match, team) for per-team rolling calculations.

    The returned DataFrame has columns: match_date, team, opponent, is_home,
    goals_scored, goals_conceded, win (int 0/1), draw (int 0/1), loss (int 0/1),
    points (int), _original_idx (int — the original df index for joining back).
    Sorted by ['team', 'match_date'] for correct rolling computation.
    """
    home_rows = pd.DataFrame(
        {
            "match_date": df["match_date"],
            "team": df["home_team"],
            "opponent": df["away_team"],
            "is_home": True,
            "goals_scored": df["full_time_home_goals"],
            "goals_conceded": df["full_time_away_goals"],
            "win": (df["result"] == "H").astype(int),
            "draw": (df["result"] == "D").astype(int),
            "loss": (df["result"] == "A").astype(int),
            "_original_idx": df.index,
        }
    )
    home_rows["points"] = home_rows["win"] * 3 + home_rows["draw"]

    away_rows = pd.DataFrame(
        {
            "match_date": df["match_date"],
            "team": df["away_team"],
            "opponent": df["home_team"],
            "is_home": False,
            "goals_scored": df["full_time_away_goals"],
            "goals_conceded": df["full_time_home_goals"],
            "win": (df["result"] == "A").astype(int),
            "draw": (df["result"] == "D").astype(int),
            "loss": (df["result"] == "H").astype(int),
            "_original_idx": df.index,
        }
    )
    away_rows["points"] = away_rows["win"] * 3 + away_rows["draw"]

    tv = pd.concat([home_rows, away_rows], ignore_index=True)
    tv = tv.sort_values(["team", "match_date"]).reset_index(drop=True)
    return tv


class BaseFeature(ABC):
    """Abstract base class for all feature modules."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this feature group."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version string for this feature implementation."""
        ...

    @property
    @abstractmethod
    def output_columns(self) -> list[str]:
        """List of column names this feature produces."""
        ...

    @property
    def dependencies(self) -> list[str]:
        """Names of feature groups that must be computed before this one."""
        return []

    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute feature columns from the accumulated DataFrame.

        Args:
            df: Full accumulated DataFrame sorted by match_date ascending with
                a 0-based integer index. Prior feature columns are present.

        Returns:
            DataFrame with the SAME INTEGER INDEX as ``df``, containing ONLY
            the new feature columns defined in ``output_columns``.
        """
        ...
