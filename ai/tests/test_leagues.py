"""Tests for the top-five league structure configuration."""

import pytest

from config.leagues import (
    TOP_FIVE_DIVISIONS,
    expected_match_count,
    expected_team_count,
    season_codes,
    season_start_year,
)


def test_top_five_divisions() -> None:
    assert TOP_FIVE_DIVISIONS == ("E0", "D1", "SP1", "I1", "F1")


def test_season_codes_spans_inclusive_range() -> None:
    assert season_codes("9899", "0102") == ["9899", "9900", "0001", "0102"]


def test_season_codes_full_backfill_range() -> None:
    codes = season_codes("0001", "2526")
    assert codes[0] == "0001"
    assert codes[-1] == "2526"
    assert len(codes) == 26


def test_season_codes_rejects_reversed_range() -> None:
    with pytest.raises(ValueError):
        season_codes("2526", "0001")


def test_season_codes_rejects_malformed_code() -> None:
    with pytest.raises(ValueError):
        season_codes("2024", "2526")


@pytest.mark.parametrize(
    ("code", "year"), [("0001", 2000), ("9899", 1998), ("2526", 2025)]
)
def test_season_start_year(code: str, year: int) -> None:
    assert season_start_year(code) == year


@pytest.mark.parametrize(
    ("division", "season", "teams"),
    [
        ("E0", "2324", 20),
        ("D1", "0001", 18),
        ("SP1", "1011", 20),
        ("I1", "0304", 18),
        ("I1", "0405", 20),
        ("F1", "0102", 18),
        ("F1", "0203", 20),
        ("F1", "2223", 20),
        ("F1", "2324", 18),
    ],
)
def test_expected_team_count(division: str, season: str, teams: int) -> None:
    assert expected_team_count(division, season) == teams


def test_expected_team_count_unknown_division_raises() -> None:
    with pytest.raises(KeyError):
        expected_team_count("E1", "2324")


def test_expected_match_count_full_season() -> None:
    assert expected_match_count("E0", "2324") == 380
    assert expected_match_count("D1", "2324") == 306


def test_expected_match_count_known_incomplete_season() -> None:
    # Ligue 1 2019/20 was abandoned in March 2020 because of COVID-19.
    assert expected_match_count("F1", "1920") == 279
