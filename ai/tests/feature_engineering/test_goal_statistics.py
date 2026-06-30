"""Tests for GoalStatisticsFeature."""

from __future__ import annotations

import math
from typing import cast

import pandas as pd
import pytest

from feature_engineering.features.goal_statistics import GoalStatisticsFeature


@pytest.fixture()
def feature() -> GoalStatisticsFeature:
    return GoalStatisticsFeature()


def test_output_columns_count(feature: GoalStatisticsFeature) -> None:
    """output_columns returns exactly 12 columns."""
    assert len(feature.output_columns) == 12


def test_output_columns_names(feature: GoalStatisticsFeature) -> None:
    """All expected column names are declared."""
    expected = {
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
    }
    assert set(feature.output_columns) == expected


def test_compute_returns_only_output_columns(
    feature: GoalStatisticsFeature, sample_matches: pd.DataFrame
) -> None:
    """compute() returns a DataFrame with exactly the declared output columns."""
    result = feature.compute(sample_matches)
    assert set(result.columns) == set(feature.output_columns)


def test_first_match_goals_are_nan(
    feature: GoalStatisticsFeature, sample_matches: pd.DataFrame
) -> None:
    """The first match for each team should have NaN goal statistics."""
    result = feature.compute(sample_matches)
    first_row = result.iloc[0]
    assert math.isnan(first_row["home_goals_scored_last5"])
    assert math.isnan(first_row["away_goals_scored_last5"])


def test_goals_scored_rolling_mean_correct(feature: GoalStatisticsFeature) -> None:
    """Rolling mean goals scored is computed correctly over prior matches."""
    # Arsenal scores 2, 1, 3 in matches 0, 1, 2 (all as home team)
    # Their 4th match (idx 3) should have goals_scored_last5 = mean(2, 1, 3) = 2.0
    rows = [
        {
            "match_date": "2023-08-01",
            "season": "2023/24",
            "competition": "PL",
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "full_time_home_goals": 2,
            "full_time_away_goals": 0,
            "result": "H",
        },
        {
            "match_date": "2023-08-08",
            "season": "2023/24",
            "competition": "PL",
            "home_team": "Arsenal",
            "away_team": "Liverpool",
            "full_time_home_goals": 1,
            "full_time_away_goals": 0,
            "result": "H",
        },
        {
            "match_date": "2023-08-15",
            "season": "2023/24",
            "competition": "PL",
            "home_team": "Arsenal",
            "away_team": "ManCity",
            "full_time_home_goals": 3,
            "full_time_away_goals": 0,
            "result": "H",
        },
        {
            "match_date": "2023-08-22",
            "season": "2023/24",
            "competition": "PL",
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "full_time_home_goals": 0,
            "full_time_away_goals": 1,
            "result": "A",
        },
    ]
    df = pd.DataFrame(rows)
    result = feature.compute(df)
    # On 4th match (idx 3), Arsenal as home has prior goals: 2, 1, 3
    val = cast(float, result.loc[3, "home_goals_scored_last5"])
    assert not math.isnan(val)
    assert abs(val - 2.0) < 1e-9
