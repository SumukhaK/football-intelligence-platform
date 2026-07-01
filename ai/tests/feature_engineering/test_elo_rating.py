"""Tests for EloRatingFeature."""

from __future__ import annotations

from typing import cast

import pandas as pd
import pytest

from feature_engineering.features.elo_rating import EloRatingFeature

_START_ELO = 1500.0


@pytest.fixture()
def feature() -> EloRatingFeature:
    return EloRatingFeature()


def test_output_columns(feature: EloRatingFeature) -> None:
    """output_columns is exactly ['home_elo_before', 'away_elo_before']."""
    assert feature.output_columns == ["home_elo_before", "away_elo_before"]


def test_first_match_both_teams_start_at_1500(
    feature: EloRatingFeature, sample_matches: pd.DataFrame
) -> None:
    """Any team playing for the first time starts at Elo 1500."""
    result = feature.compute(sample_matches)
    # First match: Arsenal vs Chelsea — both are brand new
    assert result.loc[0, "home_elo_before"] == _START_ELO
    assert result.loc[0, "away_elo_before"] == _START_ELO


def test_after_home_win_winner_elo_rises(feature: EloRatingFeature) -> None:
    """After a home win the home team's Elo in the next match is > 1500."""
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
    assert cast(float, result.loc[1, "home_elo_before"]) > _START_ELO


def test_after_away_win_loser_elo_falls(feature: EloRatingFeature) -> None:
    """After a home loss the home team's Elo in the next match is < 1500."""
    df = pd.DataFrame(
        [
            {
                "match_date": "2023-08-12",
                "season": "2023/24",
                "competition": "PL",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "full_time_home_goals": 0,
                "full_time_away_goals": 2,
                "result": "A",
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
    assert cast(float, result.loc[1, "home_elo_before"]) < _START_ELO


def test_after_draw_elos_shift(feature: EloRatingFeature) -> None:
    """After a draw, Elo values shift: the underdog gains, the favourite loses."""
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
                "match_date": "2023-08-19",
                "season": "2023/24",
                "competition": "PL",
                "home_team": "Arsenal",
                "away_team": "Liverpool",
                "full_time_home_goals": 0,
                "full_time_away_goals": 0,
                "result": "D",
            },
        ]
    )
    result = feature.compute(df)
    # After a draw between two equal teams (both at 1500) Elo stays exactly the same
    # Expected score for each = 0.5, actual = 0.5, delta = K*(0.5-0.5) = 0
    assert result.loc[1, "home_elo_before"] == _START_ELO


def test_returns_same_index(
    feature: EloRatingFeature, sample_matches: pd.DataFrame
) -> None:
    """compute() result shares the same integer index as the input."""
    result = feature.compute(sample_matches)
    assert list(result.index) == list(sample_matches.index)
