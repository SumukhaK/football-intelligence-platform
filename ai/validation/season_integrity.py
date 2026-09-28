"""Season integrity checks for one league season of canonical matches (ADR 006).

A league season is a double round robin: every team hosts every other team
exactly once. These checks catch truncated files, duplicated fixtures, wrong
season labels and results that disagree with the score.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from config.leagues import (
    KNOWN_INCOMPLETE_SEASONS,
    expected_match_count,
    expected_team_count,
    season_start_year,
)
from validation.dataset_validator import ValidationResult

# Season windows run from 1 July to 31 August of the following year, which
# covers the COVID-delayed end of 2019/20.
_WINDOW_START = (7, 1)
_WINDOW_END = (8, 31)


def check_season_integrity(
    df: pd.DataFrame, division: str, season_code: str
) -> ValidationResult:
    """Validate one division season of canonical ``ProcessedMatch`` rows."""
    result = ValidationResult()
    label = f"{division} {season_code}"
    _check_team_count(df, division, season_code, label, result)
    _check_fixtures(df, division, season_code, label, result)
    _check_results(df, label, result)
    _check_dates(df, season_code, label, result)
    return result


def check_partial_season(
    df: pd.DataFrame, division: str, season_code: str
) -> ValidationResult:
    """Validate a season still in progress: no match or schedule counts.

    Duplicate fixtures, results that disagree with the score and dates outside
    the season window still fail, and the league may not have more teams than
    its size.
    """
    result = ValidationResult()
    label = f"{division} {season_code}"
    teams = set(df["home_team"]) | set(df["away_team"])
    expected = expected_team_count(division, season_code)
    if len(teams) > expected:
        result.add_error(f"{label}: {len(teams)} teams, expected at most {expected}")
    duplicated = df.duplicated(["home_team", "away_team"], keep=False)
    if duplicated.any():
        pairs = df.loc[duplicated, ["home_team", "away_team"]].drop_duplicates()
        result.add_error(f"{label}: duplicate fixtures {pairs.values.tolist()}")
    _check_results(df, label, result)
    _check_dates(df, season_code, label, result)
    return result


def _check_team_count(
    df: pd.DataFrame, division: str, season: str, label: str, result: ValidationResult
) -> None:
    """Fail when the number of distinct teams differs from the league's size."""
    teams = set(df["home_team"]) | set(df["away_team"])
    expected = expected_team_count(division, season)
    if len(teams) != expected:
        result.add_error(f"{label}: {len(teams)} teams, expected {expected}")


def _check_fixtures(
    df: pd.DataFrame, division: str, season: str, label: str, result: ValidationResult
) -> None:
    """Fail on duplicate fixtures, wrong match counts or unbalanced schedules."""
    duplicated = df.duplicated(["home_team", "away_team"], keep=False)
    if duplicated.any():
        pairs = df.loc[duplicated, ["home_team", "away_team"]].drop_duplicates()
        result.add_error(f"{label}: duplicate fixtures {pairs.values.tolist()}")

    expected = expected_match_count(division, season)
    if len(df) != expected:
        result.add_error(f"{label}: {len(df)} matches, expected {expected}")

    if (division, season) in KNOWN_INCOMPLETE_SEASONS:
        result.add_warning(f"{label}: known incomplete season, schedule not checked")
        return

    per_team = expected_team_count(division, season) - 1
    for side in ("home_team", "away_team"):
        counts = df[side].value_counts()
        off = counts[counts != per_team]
        if not off.empty:
            where = side.split("_")[0]
            result.add_error(
                f"{label}: {where} match counts differ from {per_team}: "
                f"{off.to_dict()}"
            )


def _check_results(df: pd.DataFrame, label: str, result: ValidationResult) -> None:
    """Fail when the recorded result disagrees with the final score."""
    home, away = df["full_time_home_goals"], df["full_time_away_goals"]
    derived = (
        pd.Series("D", index=df.index).mask(home > away, "H").mask(away > home, "A")
    )
    wrong = df[derived != df["result"]]
    if not wrong.empty:
        rows = wrong[["match_date", "home_team", "away_team"]].astype(str)
        result.add_error(f"{label}: result disagrees with goals {rows.values.tolist()}")


def _check_dates(
    df: pd.DataFrame, season_code: str, label: str, result: ValidationResult
) -> None:
    """Fail when any match date falls outside the season window."""
    start_year = season_start_year(season_code)
    start = date(start_year, *_WINDOW_START)
    end = date(start_year + 1, *_WINDOW_END)
    dates = pd.to_datetime(df["match_date"]).dt.date
    outside = df[(dates < start) | (dates > end)]
    if not outside.empty:
        rows = outside[["match_date", "home_team", "away_team"]].astype(str)
        result.add_error(
            f"{label}: matches outside {start} to {end}: {rows.values.tolist()}"
        )
