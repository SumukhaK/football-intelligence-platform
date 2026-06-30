"""Tests for feature engineering validators."""

from __future__ import annotations

import pandas as pd

from feature_engineering.validators import (
    validate_canonical_input,
    validate_feature_matrix,
)

_REQUIRED_COLS = [
    "match_date",
    "season",
    "competition",
    "home_team",
    "away_team",
    "full_time_home_goals",
    "full_time_away_goals",
    "result",
]


def _minimal_valid_df() -> pd.DataFrame:
    """Return a minimal valid canonical DataFrame."""
    return pd.DataFrame(
        {
            "match_date": ["2023-08-12"],
            "season": ["2023/24"],
            "competition": ["Premier League"],
            "home_team": ["Arsenal"],
            "away_team": ["Chelsea"],
            "full_time_home_goals": [2],
            "full_time_away_goals": [1],
            "result": ["H"],
        }
    )


# ---------------------------------------------------------------------------
# validate_canonical_input tests
# ---------------------------------------------------------------------------


def test_valid_canonical_df_passes() -> None:
    """A well-formed canonical DataFrame passes without errors."""
    result = validate_canonical_input(_minimal_valid_df())
    assert result.passed
    assert result.errors == []


def test_missing_required_column_fails() -> None:
    """Removing a required column triggers a validation error."""
    df = _minimal_valid_df().drop(columns=["home_team"])
    result = validate_canonical_input(df)
    assert not result.passed
    assert any("home_team" in e for e in result.errors)


def test_null_in_required_column_fails() -> None:
    """A null value in a required column triggers a validation error."""
    df = _minimal_valid_df()
    df.loc[0, "season"] = None
    result = validate_canonical_input(df)
    assert not result.passed
    assert any("season" in e for e in result.errors)


def test_empty_dataframe_fails() -> None:
    """An empty DataFrame fails the row-count check."""
    df = pd.DataFrame(columns=_REQUIRED_COLS)
    result = validate_canonical_input(df)
    assert not result.passed


def test_invalid_result_value_fails() -> None:
    """A result value outside {'H','D','A'} triggers a validation error."""
    df = _minimal_valid_df()
    df.loc[0, "result"] = "X"
    result = validate_canonical_input(df)
    assert not result.passed
    assert any("invalid" in e.lower() or "result" in e for e in result.errors)


# ---------------------------------------------------------------------------
# validate_feature_matrix tests
# ---------------------------------------------------------------------------


def test_valid_feature_matrix_passes() -> None:
    """A DataFrame that contains all required features passes."""
    df = pd.DataFrame(
        {
            "home_form_wins_last5": [1.0],
            "away_form_wins_last5": [0.0],
        }
    )
    required = ["home_form_wins_last5", "away_form_wins_last5"]
    result = validate_feature_matrix(df, required)
    assert result.passed


def test_feature_matrix_missing_required_feature_fails() -> None:
    """A DataFrame missing a declared required feature column fails."""
    df = pd.DataFrame({"home_form_wins_last5": [1.0]})
    required = ["home_form_wins_last5", "away_form_wins_last5"]
    result = validate_feature_matrix(df, required)
    assert not result.passed
    assert any("away_form_wins_last5" in e for e in result.errors)


def test_feature_matrix_all_nan_column_passes_with_warning() -> None:
    """An all-NaN feature column passes but emits a warning."""
    df = pd.DataFrame(
        {
            "home_form_wins_last5": [float("nan")],
            "away_form_wins_last5": [0.0],
        }
    )
    required = ["home_form_wins_last5", "away_form_wins_last5"]
    result = validate_feature_matrix(df, required)
    assert result.passed
    assert any("home_form_wins_last5" in w for w in result.warnings)
