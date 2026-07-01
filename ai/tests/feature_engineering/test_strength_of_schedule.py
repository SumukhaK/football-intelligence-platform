"""Tests for StrengthOfScheduleFeature."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from feature_engineering.features.strength_of_schedule import StrengthOfScheduleFeature


@pytest.fixture()
def feature() -> StrengthOfScheduleFeature:
    return StrengthOfScheduleFeature()


def test_output_columns_count(feature: StrengthOfScheduleFeature) -> None:
    """output_columns returns exactly 4 columns."""
    assert len(feature.output_columns) == 4


def test_output_columns_names(feature: StrengthOfScheduleFeature) -> None:
    """All expected column names are declared."""
    expected = {
        "home_avg_opp_elo_last5",
        "home_avg_opp_elo_last10",
        "away_avg_opp_elo_last5",
        "away_avg_opp_elo_last10",
    }
    assert set(feature.output_columns) == expected


def test_dependencies_includes_elo_rating(feature: StrengthOfScheduleFeature) -> None:
    """dependencies declares 'elo_rating' as a required predecessor."""
    assert "elo_rating" in feature.dependencies


def test_first_match_is_nan(
    feature: StrengthOfScheduleFeature, elo_enriched_matches: pd.DataFrame
) -> None:
    """First match per team has NaN strength-of-schedule (no prior opponent elos)."""
    result = feature.compute(elo_enriched_matches)
    first_row = result.iloc[0]
    # At least one of the two teams is playing their first match
    assert math.isnan(first_row["home_avg_opp_elo_last5"])


def test_later_matches_have_non_nan_values(
    feature: StrengthOfScheduleFeature, elo_enriched_matches: pd.DataFrame
) -> None:
    """After 2+ matches for a team, strength-of-schedule is a real number."""
    result = feature.compute(elo_enriched_matches)
    # The last match in the fixture should have non-NaN values for at least one team
    last_row = result.iloc[-1]
    has_real_value = not math.isnan(
        last_row["home_avg_opp_elo_last5"]
    ) or not math.isnan(last_row["away_avg_opp_elo_last5"])
    assert has_real_value


def test_returns_only_output_columns(
    feature: StrengthOfScheduleFeature, elo_enriched_matches: pd.DataFrame
) -> None:
    """compute() returns a DataFrame with exactly the declared output columns."""
    result = feature.compute(elo_enriched_matches)
    assert set(result.columns) == set(feature.output_columns)


def test_returns_same_index(
    feature: StrengthOfScheduleFeature, elo_enriched_matches: pd.DataFrame
) -> None:
    """compute() result shares the same integer index as the input."""
    result = feature.compute(elo_enriched_matches)
    assert list(result.index) == list(elo_enriched_matches.index)
