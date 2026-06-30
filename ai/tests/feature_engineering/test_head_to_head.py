"""Tests for HeadToHeadFeature."""

from __future__ import annotations

import pandas as pd
import pytest

from feature_engineering.features.head_to_head import HeadToHeadFeature


@pytest.fixture()
def feature() -> HeadToHeadFeature:
    return HeadToHeadFeature()


def test_output_columns(feature: HeadToHeadFeature) -> None:
    """output_columns is exactly the 4 h2h columns."""
    assert feature.output_columns == [
        "h2h_meetings",
        "h2h_home_wins",
        "h2h_away_wins",
        "h2h_draws",
    ]


def test_first_meeting_all_zeros(feature: HeadToHeadFeature) -> None:
    """The first meeting between two teams has all zeros."""
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
            }
        ]
    )
    result = feature.compute(df)
    row = result.iloc[0]
    assert row["h2h_meetings"] == 0
    assert row["h2h_home_wins"] == 0
    assert row["h2h_away_wins"] == 0
    assert row["h2h_draws"] == 0


def test_after_one_home_win_h2h_home_wins_is_one(feature: HeadToHeadFeature) -> None:
    """After 1 prior Arsenal home win, h2h_meetings=1 and h2h_home_wins=1."""
    df = pd.DataFrame(
        [
            {
                "match_date": "2023-08-12",
                "season": "2023/24",
                "competition": "PL",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "full_time_home_goals": 2,
                "full_time_away_goals": 0,
                "result": "H",
            },
            {
                "match_date": "2023-09-12",
                "season": "2023/24",
                "competition": "PL",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "full_time_home_goals": 1,
                "full_time_away_goals": 1,
                "result": "D",
            },
        ]
    )
    result = feature.compute(df)
    second = result.iloc[1]
    assert second["h2h_meetings"] == 1
    assert second["h2h_home_wins"] == 1
    assert second["h2h_away_wins"] == 0
    assert second["h2h_draws"] == 0


def test_draw_increments_draws(feature: HeadToHeadFeature) -> None:
    """After 1 prior draw, h2h_draws=1 on the next meeting."""
    df = pd.DataFrame(
        [
            {
                "match_date": "2023-08-12",
                "season": "2023/24",
                "competition": "PL",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "full_time_home_goals": 1,
                "full_time_away_goals": 1,
                "result": "D",
            },
            {
                "match_date": "2023-09-12",
                "season": "2023/24",
                "competition": "PL",
                "home_team": "Chelsea",
                "away_team": "Arsenal",
                "full_time_home_goals": 0,
                "full_time_away_goals": 2,
                "result": "A",
            },
        ]
    )
    result = feature.compute(df)
    second = result.iloc[1]
    assert second["h2h_meetings"] == 1
    assert second["h2h_draws"] == 1


def test_returns_same_index(
    feature: HeadToHeadFeature, sample_matches: pd.DataFrame
) -> None:
    """compute() result shares the same integer index as the input."""
    result = feature.compute(sample_matches)
    assert list(result.index) == list(sample_matches.index)
