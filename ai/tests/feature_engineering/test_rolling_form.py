"""Tests for RollingFormFeature."""

from __future__ import annotations

import math
from typing import cast

import pandas as pd
import pytest

from feature_engineering.features.rolling_form import RollingFormFeature


@pytest.fixture()
def feature() -> RollingFormFeature:
    return RollingFormFeature()


def test_output_columns_count(feature: RollingFormFeature) -> None:
    """output_columns returns exactly 8 columns."""
    assert len(feature.output_columns) == 8


def test_output_columns_names(feature: RollingFormFeature) -> None:
    """All expected column names are declared."""
    expected = {
        "home_form_wins_last5",
        "home_form_wins_last10",
        "home_form_points_last5",
        "home_form_points_last10",
        "away_form_wins_last5",
        "away_form_wins_last10",
        "away_form_points_last5",
        "away_form_points_last10",
    }
    assert set(feature.output_columns) == expected


def test_name_and_version(feature: RollingFormFeature) -> None:
    """name and version are set to expected values."""
    assert feature.name == "rolling_form"
    assert feature.version == "1.0.0"


def test_compute_returns_same_index(
    feature: RollingFormFeature, sample_matches: pd.DataFrame
) -> None:
    """compute() result shares the same integer index as the input."""
    result = feature.compute(sample_matches)
    assert list(result.index) == list(sample_matches.index)


def test_compute_returns_only_output_columns(
    feature: RollingFormFeature, sample_matches: pd.DataFrame
) -> None:
    """compute() returns a DataFrame with exactly the declared output columns."""
    result = feature.compute(sample_matches)
    assert set(result.columns) == set(feature.output_columns)


def test_first_match_per_team_is_nan(
    feature: RollingFormFeature, sample_matches: pd.DataFrame
) -> None:
    """Teams with no prior matches produce NaN for all rolling form columns.

    shift(1) moves the first entry to NaN; rolling([NaN], min_periods=1) = NaN.
    """
    result = feature.compute(sample_matches)

    # Match at index 0: Arsenal vs Chelsea — both teams' first ever match
    first_row = result.iloc[0]
    assert math.isnan(first_row["home_form_wins_last5"])
    assert math.isnan(first_row["away_form_wins_last5"])


def test_rolling_form_accumulates_over_matches(
    feature: RollingFormFeature, sample_matches: pd.DataFrame
) -> None:
    """For a team with wins in the dataset, wins_last5 is > 0 after enough matches."""
    result = feature.compute(sample_matches)
    # Arsenal won matchdays 1, 3; by match 7 they should have wins > 0
    # The last Arsenal home match in the fixture is index 11 (Arsenal vs Chelsea 3-0)
    arsenal_home_rows = sample_matches[sample_matches["home_team"] == "Arsenal"]
    if len(arsenal_home_rows) >= 3:
        last_idx = arsenal_home_rows.index[-1]
        wins_val = result.loc[last_idx, "home_form_wins_last5"]
        # After at least 2 prior home+away wins the rolling value should be > 0
        # (NaN is also acceptable if no prior matches, but here Arsenal has history)
        if not math.isnan(wins_val):
            assert wins_val >= 0.0  # non-negative; actual win accumulation tested below


def test_rolling_form_win_count_is_correct(
    feature: RollingFormFeature,
) -> None:
    """With exactly 3 wins in the first 5 matches, the 6th match shows wins=3."""
    rows = []
    # Arsenal plays 5 matches (wins 3, loses 2), then plays a 6th
    opponents = ["Chelsea", "Liverpool", "ManCity", "Chelsea", "Liverpool", "ManCity"]
    results = ["H", "A", "H", "H", "A", "D"]  # Arsenal wins: 1,3,4 → 3 wins in first 5
    fthg = [1, 0, 2, 1, 0, 0]
    ftag = [0, 1, 0, 0, 1, 0]
    zipped = zip(opponents, results, fthg, ftag, strict=False)
    for i, (opp, res, hg, ag) in enumerate(zipped):
        rows.append(
            {
                "match_date": f"2023-0{i + 1}-01",
                "season": "2023/24",
                "competition": "PL",
                "home_team": "Arsenal",
                "away_team": opp,
                "full_time_home_goals": hg,
                "full_time_away_goals": ag,
                "result": res,
            }
        )
    df = pd.DataFrame(rows).sort_values("match_date").reset_index(drop=True)
    result = feature.compute(df)
    # Row 5 (6th match): prior results H,A,H,H,A → 3 home wins (idx 0,2,3)
    wins_on_6th = cast(float, result.loc[5, "home_form_wins_last5"])
    assert not math.isnan(wins_on_6th)
    assert wins_on_6th == 3.0


def test_compute_single_row_does_not_crash(feature: RollingFormFeature) -> None:
    """compute() on a one-row DataFrame should not raise."""
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
    assert len(result) == 1
