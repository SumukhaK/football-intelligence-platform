"""Tests for LeaguePositionFeature."""

from __future__ import annotations

import pandas as pd
import pytest

from feature_engineering.features.league_position import LeaguePositionFeature


@pytest.fixture()
def feature() -> LeaguePositionFeature:
    return LeaguePositionFeature()


def test_output_columns_count(feature: LeaguePositionFeature) -> None:
    """output_columns returns exactly 6 columns."""
    assert len(feature.output_columns) == 6


def test_output_columns_names(feature: LeaguePositionFeature) -> None:
    """All expected column names are declared."""
    expected = {
        "home_league_position",
        "away_league_position",
        "home_league_points",
        "away_league_points",
        "home_matches_played",
        "away_matches_played",
    }
    assert set(feature.output_columns) == expected


def test_before_any_matches_all_teams_position_one(
    feature: LeaguePositionFeature, sample_matches: pd.DataFrame
) -> None:
    """At the very first match of the season all teams start at position 1, 0 points."""
    result = feature.compute(sample_matches)
    first_row = result.iloc[0]
    assert first_row["home_league_position"] == 1
    assert first_row["away_league_position"] == 1
    assert first_row["home_league_points"] == 0
    assert first_row["away_league_points"] == 0


def test_points_update_reflected_in_next_match(feature: LeaguePositionFeature) -> None:
    """After a home win, the home team's points in the NEXT match reflect that win."""
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
                "match_date": "2023-08-19",
                "season": "2023/24",
                "competition": "PL",
                "home_team": "Arsenal",
                "away_team": "Liverpool",
                "full_time_home_goals": 1,
                "full_time_away_goals": 0,
                "result": "H",
            },
        ]
    )
    result = feature.compute(df)
    # Arsenal won match 0; their points at match 1 should be 3
    assert result.loc[1, "home_league_points"] == 3


def test_matches_played_increments(feature: LeaguePositionFeature) -> None:
    """matches_played for a team increments by 1 after each match."""
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
            {
                "match_date": "2023-08-26",
                "season": "2023/24",
                "competition": "PL",
                "home_team": "Arsenal",
                "away_team": "ManCity",
                "full_time_home_goals": 0,
                "full_time_away_goals": 0,
                "result": "D",
            },
        ]
    )
    result = feature.compute(df)
    assert result.loc[0, "home_matches_played"] == 0
    assert result.loc[1, "home_matches_played"] == 1
    assert result.loc[2, "home_matches_played"] == 2


def test_returns_same_index(
    feature: LeaguePositionFeature, sample_matches: pd.DataFrame
) -> None:
    """compute() result shares the same integer index as the input."""
    result = feature.compute(sample_matches)
    assert list(result.index) == list(sample_matches.index)
