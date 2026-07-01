"""Shared fixtures for feature engineering tests."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from feature_engineering.features.elo_rating import EloRatingFeature

TEAMS = ["Arsenal", "Chelsea", "Liverpool", "ManCity"]


def make_match(
    dt: date,
    ht: str,
    at: str,
    fthg: int,
    ftag: int,
    result: str,
) -> dict[str, object]:
    """Build a single match record dict."""
    return {
        "match_date": str(dt),
        "season": "2023/24",
        "competition": "Premier League",
        "home_team": ht,
        "away_team": at,
        "full_time_home_goals": fthg,
        "full_time_away_goals": ftag,
        "result": result,
    }


@pytest.fixture()
def sample_matches() -> pd.DataFrame:
    """Deterministic fixture with 16 matches across 4 teams, sorted by date."""
    rows = [
        # Matchday 1
        make_match(date(2023, 8, 12), "Arsenal", "Chelsea", 2, 1, "H"),
        make_match(date(2023, 8, 12), "Liverpool", "ManCity", 1, 1, "D"),
        # Matchday 2
        make_match(date(2023, 8, 19), "Chelsea", "Liverpool", 0, 2, "A"),
        make_match(date(2023, 8, 19), "ManCity", "Arsenal", 3, 1, "H"),
        # Matchday 3
        make_match(date(2023, 8, 26), "Arsenal", "Liverpool", 1, 0, "H"),
        make_match(date(2023, 8, 26), "Chelsea", "ManCity", 2, 2, "D"),
        # Matchday 4
        make_match(date(2023, 9, 2), "ManCity", "Chelsea", 1, 0, "H"),
        make_match(date(2023, 9, 2), "Liverpool", "Arsenal", 2, 1, "H"),
        # Matchday 5
        make_match(date(2023, 9, 16), "Arsenal", "ManCity", 0, 0, "D"),
        make_match(date(2023, 9, 16), "Chelsea", "Liverpool", 1, 3, "A"),
        # Matchday 6
        make_match(date(2023, 9, 23), "ManCity", "Liverpool", 2, 1, "H"),
        make_match(date(2023, 9, 23), "Arsenal", "Chelsea", 3, 0, "H"),
        # Matchday 7
        make_match(date(2023, 9, 30), "Liverpool", "Chelsea", 1, 1, "D"),
        make_match(date(2023, 9, 30), "ManCity", "Arsenal", 2, 0, "H"),
        # Matchday 8
        make_match(date(2023, 10, 7), "Chelsea", "Arsenal", 0, 1, "A"),
        make_match(date(2023, 10, 7), "Liverpool", "ManCity", 0, 2, "A"),
    ]
    df = pd.DataFrame(rows)
    df = df.sort_values("match_date").reset_index(drop=True)
    return df


@pytest.fixture()
def elo_enriched_matches(sample_matches: pd.DataFrame) -> pd.DataFrame:
    """sample_matches with EloRating columns appended — for StrengthOfSchedule tests."""
    elo_feature = EloRatingFeature()
    elo_cols = elo_feature.compute(sample_matches)
    return pd.concat([sample_matches, elo_cols], axis=1)
