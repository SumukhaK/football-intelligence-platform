"""Tests for HomeAdvantageFeature."""

from __future__ import annotations

import pandas as pd
import pytest

from feature_engineering.features.home_advantage import HomeAdvantageFeature


@pytest.fixture()
def feature() -> HomeAdvantageFeature:
    return HomeAdvantageFeature()


def test_output_columns(feature: HomeAdvantageFeature) -> None:
    """output_columns is exactly ['home_win_pct', 'home_ppg']."""
    assert feature.output_columns == ["home_win_pct", "home_ppg"]


def test_first_home_game_is_zero(feature: HomeAdvantageFeature) -> None:
    """A team with no prior home history gets 0.0 for home_win_pct and home_ppg."""
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
            }
        ]
    )
    result = feature.compute(df)
    assert result.loc[0, "home_win_pct"] == 0.0
    assert result.loc[0, "home_ppg"] == 0.0


def test_home_win_pct_positive_after_wins(
    feature: HomeAdvantageFeature, sample_matches: pd.DataFrame
) -> None:
    """After a team has won home games, home_win_pct > 0 on a subsequent home match."""
    result = feature.compute(sample_matches)
    # Arsenal's later home matches should reflect prior home wins
    arsenal_home = sample_matches[sample_matches["home_team"] == "Arsenal"]
    assert len(arsenal_home) >= 3
    later_idx = arsenal_home.index[2]  # 3rd home match for Arsenal
    assert result.loc[later_idx, "home_win_pct"] > 0.0


def test_returns_same_index(
    feature: HomeAdvantageFeature, sample_matches: pd.DataFrame
) -> None:
    """compute() result shares the same integer index as the input."""
    result = feature.compute(sample_matches)
    assert list(result.index) == list(sample_matches.index)
