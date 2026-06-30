"""Tests for RestDaysFeature."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from feature_engineering.features.rest_days import RestDaysFeature


@pytest.fixture()
def feature() -> RestDaysFeature:
    return RestDaysFeature()


def test_output_columns(feature: RestDaysFeature) -> None:
    """output_columns is exactly ['home_rest_days', 'away_rest_days']."""
    assert feature.output_columns == ["home_rest_days", "away_rest_days"]


def test_first_match_rest_days_is_nan(
    feature: RestDaysFeature, sample_matches: pd.DataFrame
) -> None:
    """A team's first match has NaN rest days (no prior match to measure from)."""
    result = feature.compute(sample_matches)
    # First row: Arsenal (home) and Chelsea (away) — both teams' first appearance
    first_row = result.iloc[0]
    assert math.isnan(first_row["home_rest_days"])
    assert math.isnan(first_row["away_rest_days"])


def test_rest_days_seven_days_apart(feature: RestDaysFeature) -> None:
    """Team plays 2023-08-12 then 2023-08-19 → rest_days = 7 for the second match."""
    df = pd.DataFrame(
        [
            {
                "match_date": "2023-08-12",
                "season": "2023/24",
                "competition": "PL",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "full_time_home_goals": 1,
                "full_time_away_goals": 0,
                "result": "H",
            },
            {
                "match_date": "2023-08-19",
                "season": "2023/24",
                "competition": "PL",
                "home_team": "Arsenal",
                "away_team": "Liverpool",
                "full_time_home_goals": 2,
                "full_time_away_goals": 1,
                "result": "H",
            },
        ]
    )
    result = feature.compute(df)
    assert result.loc[1, "home_rest_days"] == 7.0


def test_returns_same_index(
    feature: RestDaysFeature, sample_matches: pd.DataFrame
) -> None:
    """compute() result shares the same integer index as the input."""
    result = feature.compute(sample_matches)
    assert list(result.index) == list(sample_matches.index)
