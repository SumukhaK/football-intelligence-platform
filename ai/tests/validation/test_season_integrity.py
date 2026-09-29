"""Tests for per-league season integrity checks (ADR 006)."""

from __future__ import annotations

from datetime import date, timedelta
from itertools import permutations

import pandas as pd
import pytest

from validation.season_integrity import check_partial_season, check_season_integrity


def _season(teams: list[str], start: date = date(2023, 8, 12)) -> pd.DataFrame:
    """Build a complete double round-robin season with home wins."""
    rows = []
    for i, (home, away) in enumerate(permutations(teams, 2)):
        rows.append(
            {
                "match_date": start + timedelta(days=i),
                "home_team": home,
                "away_team": away,
                "full_time_home_goals": 1,
                "full_time_away_goals": 0,
                "result": "H",
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture()
def bundesliga() -> pd.DataFrame:
    return _season([f"Team {i}" for i in range(18)])


def test_complete_season_passes(bundesliga: pd.DataFrame) -> None:
    result = check_season_integrity(bundesliga, "D1", "2324")
    assert result.passed, str(result)


def test_wrong_team_count_fails() -> None:
    df = _season([f"Team {i}" for i in range(20)])
    result = check_season_integrity(df, "D1", "2324")
    assert not result.passed
    assert any("20 teams" in e for e in result.errors)


def test_missing_match_fails(bundesliga: pd.DataFrame) -> None:
    result = check_season_integrity(bundesliga.iloc[1:], "D1", "2324")
    assert not result.passed
    assert any("305 matches" in e for e in result.errors)
    assert any("home" in e for e in result.errors)


def test_duplicate_fixture_fails(bundesliga: pd.DataFrame) -> None:
    df = pd.concat([bundesliga, bundesliga.iloc[[0]]], ignore_index=True)
    result = check_season_integrity(df, "D1", "2324")
    assert not result.passed
    assert any("duplicate" in e for e in result.errors)


def test_result_inconsistent_with_goals_fails(bundesliga: pd.DataFrame) -> None:
    df = bundesliga.copy()
    df.loc[0, "result"] = "A"
    result = check_season_integrity(df, "D1", "2324")
    assert not result.passed
    assert any("result" in e for e in result.errors)


def test_date_outside_season_window_fails(bundesliga: pd.DataFrame) -> None:
    df = bundesliga.copy()
    df.loc[0, "match_date"] = date(2025, 1, 1)
    result = check_season_integrity(df, "D1", "2324")
    assert not result.passed
    assert any("outside" in e for e in result.errors)


def test_known_incomplete_season_passes_with_expected_count() -> None:
    df = _season([f"Team {i}" for i in range(20)], start=date(2019, 8, 9))
    result = check_season_integrity(df.iloc[:279], "F1", "1920")
    assert result.passed, str(result)
    assert result.warnings


def test_accepts_iso_date_strings(bundesliga: pd.DataFrame) -> None:
    df = bundesliga.copy()
    df["match_date"] = df["match_date"].astype(str)
    assert check_season_integrity(df, "D1", "2324").passed


class TestPartialSeason:
    def test_partial_season_passes_with_fewer_matches(
        self, bundesliga: pd.DataFrame
    ) -> None:
        result = check_partial_season(bundesliga.iloc[:60], "D1", "2324")
        assert result.passed, str(result)

    def test_partial_season_still_rejects_duplicates(
        self, bundesliga: pd.DataFrame
    ) -> None:
        df = pd.concat([bundesliga.iloc[:10], bundesliga.iloc[[0]]])
        result = check_partial_season(df, "D1", "2324")
        assert any("duplicate" in e for e in result.errors)

    def test_partial_season_rejects_too_many_teams(self) -> None:
        df = _season([f"Team {i}" for i in range(20)]).iloc[:200]
        result = check_partial_season(df, "D1", "2324")
        assert any("20 teams" in e for e in result.errors)

    def test_partial_season_checks_results_and_dates(
        self, bundesliga: pd.DataFrame
    ) -> None:
        df = bundesliga.iloc[:5].copy()
        df.loc[0, "result"] = "D"
        df.loc[1, "match_date"] = date(2030, 1, 1)
        result = check_partial_season(df, "D1", "2324")
        assert any("result" in e for e in result.errors)
        assert any("outside" in e for e in result.errors)
