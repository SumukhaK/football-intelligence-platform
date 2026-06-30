"""Tests for canonical match schemas and MatchNormalizer."""

from datetime import date

import pandas as pd
import pytest
from pydantic import ValidationError as PydanticValidationError

from schemas.match import (
    DIVISION_TO_COMPETITION,
    MatchNormalizer,
    ProcessedMatch,
    RawMatch,
    parse_match_date,
    season_label,
)

# ---------------------------------------------------------------------------
# parse_match_date
# ---------------------------------------------------------------------------


def test_parse_match_date_yyyy_format() -> None:
    assert parse_match_date("12/08/2023") == date(2023, 8, 12)


def test_parse_match_date_yy_format() -> None:
    assert parse_match_date("12/08/23") == date(2023, 8, 12)


def test_parse_match_date_strips_whitespace() -> None:
    assert parse_match_date("  01/01/2024  ") == date(2024, 1, 1)


def test_parse_match_date_invalid_raises() -> None:
    with pytest.raises(ValueError, match="Cannot parse date"):
        parse_match_date("2023-08-12")


# ---------------------------------------------------------------------------
# season_label
# ---------------------------------------------------------------------------


def test_season_label_current_season() -> None:
    assert season_label("2324") == "2023/24"


def test_season_label_earlier_season() -> None:
    assert season_label("2223") == "2022/23"


def test_season_label_invalid_length_raises() -> None:
    with pytest.raises(ValueError, match="Invalid season code"):
        season_label("234")


def test_season_label_non_digit_raises() -> None:
    with pytest.raises(ValueError, match="Invalid season code"):
        season_label("23ab")


# ---------------------------------------------------------------------------
# DIVISION_TO_COMPETITION
# ---------------------------------------------------------------------------


def test_division_to_competition_premier_league() -> None:
    assert DIVISION_TO_COMPETITION["E0"] == "Premier League"


def test_division_to_competition_championship() -> None:
    assert DIVISION_TO_COMPETITION["E1"] == "Championship"


# ---------------------------------------------------------------------------
# RawMatch
# ---------------------------------------------------------------------------


def test_raw_match_minimal_valid() -> None:
    m = RawMatch(
        date="01/08/2023",
        home_team="Arsenal",
        away_team="Nottm Forest",
        home_goals_ft=2,
        away_goals_ft=1,
        result_ft="H",
    )
    assert m.home_team == "Arsenal"
    assert m.odds_b365_home is None


def test_raw_match_invalid_result_raises() -> None:
    with pytest.raises(PydanticValidationError):
        RawMatch(
            date="01/08/2023",
            home_team="A",
            away_team="B",
            home_goals_ft=0,
            away_goals_ft=0,
            result_ft="X",  # type: ignore[arg-type]  # intentional invalid value
        )


def test_raw_match_frozen() -> None:
    m = RawMatch(
        date="01/08/2023",
        home_team="Arsenal",
        away_team="Nottm Forest",
        home_goals_ft=2,
        away_goals_ft=1,
        result_ft="H",
    )
    with pytest.raises(PydanticValidationError):
        m.home_team = "Chelsea"


# ---------------------------------------------------------------------------
# ProcessedMatch
# ---------------------------------------------------------------------------


def test_processed_match_all_fields() -> None:
    m = ProcessedMatch(
        match_date=date(2023, 8, 12),
        season="2023/24",
        competition="Premier League",
        home_team="Arsenal",
        away_team="Nottm Forest",
        full_time_home_goals=2,
        full_time_away_goals=1,
        result="H",
        home_shots=12,
        away_shots=8,
        home_odds=1.95,
        draw_odds=3.5,
        away_odds=4.2,
    )
    assert m.result == "H"
    assert m.home_shots == 12


def test_processed_match_negative_goals_raises() -> None:
    with pytest.raises(PydanticValidationError):
        ProcessedMatch(
            match_date=date(2023, 8, 12),
            season="2023/24",
            competition="Premier League",
            home_team="Arsenal",
            away_team="Nottm Forest",
            full_time_home_goals=-1,
            full_time_away_goals=0,
            result="A",
        )


def test_processed_match_zero_odds_raises() -> None:
    with pytest.raises(PydanticValidationError):
        ProcessedMatch(
            match_date=date(2023, 8, 12),
            season="2023/24",
            competition="Premier League",
            home_team="Arsenal",
            away_team="Nottm Forest",
            full_time_home_goals=0,
            full_time_away_goals=1,
            result="A",
            home_odds=0.0,  # must be gt=0
        )


# ---------------------------------------------------------------------------
# MatchNormalizer.normalise_row
# ---------------------------------------------------------------------------


@pytest.fixture()
def normalizer() -> MatchNormalizer:
    return MatchNormalizer()


def test_normalise_row_minimal(normalizer: MatchNormalizer) -> None:
    row = {
        "date": "12/08/2023",
        "home_team": "Arsenal",
        "away_team": "Nottm Forest",
        "home_goals_ft": 2,
        "away_goals_ft": 1,
        "result_ft": "H",
    }
    m = normalizer.normalise_row(row, season_code="2324", division="E0")
    assert m.match_date == date(2023, 8, 12)
    assert m.season == "2023/24"
    assert m.competition == "Premier League"
    assert m.full_time_home_goals == 2
    assert m.home_shots is None
    assert m.home_odds is None


def test_normalise_row_with_optional_stats(normalizer: MatchNormalizer) -> None:
    row = {
        "date": "12/08/2023",
        "home_team": "Arsenal",
        "away_team": "Nottm Forest",
        "home_goals_ft": 2,
        "away_goals_ft": 1,
        "result_ft": "H",
        "home_goals_ht": 1,
        "away_goals_ht": 0,
        "home_shots": 12,
        "away_shots": 8,
        "odds_b365_home": 1.95,
        "odds_b365_draw": 3.5,
        "odds_b365_away": 4.2,
    }
    m = normalizer.normalise_row(row, season_code="2324", division="E0")
    assert m.half_time_home_goals == 1
    assert m.home_shots == 12
    assert m.home_odds == pytest.approx(1.95)


def test_normalise_row_nan_optional_becomes_none(normalizer: MatchNormalizer) -> None:
    import numpy as np

    row = {
        "date": "12/08/2023",
        "home_team": "Arsenal",
        "away_team": "Nottm Forest",
        "home_goals_ft": 2,
        "away_goals_ft": 1,
        "result_ft": "H",
        "home_shots": float("nan"),
        "odds_b365_home": np.nan,
    }
    m = normalizer.normalise_row(row, season_code="2324", division="E0")
    assert m.home_shots is None
    assert m.home_odds is None


def test_normalise_row_unknown_division_uses_code(normalizer: MatchNormalizer) -> None:
    row = {
        "date": "12/08/2023",
        "home_team": "A",
        "away_team": "B",
        "home_goals_ft": 0,
        "away_goals_ft": 0,
        "result_ft": "D",
    }
    m = normalizer.normalise_row(row, season_code="2324", division="XX")
    assert m.competition == "XX"


def test_normalise_row_bad_date_raises(normalizer: MatchNormalizer) -> None:
    row = {
        "date": "not-a-date",
        "home_team": "A",
        "away_team": "B",
        "home_goals_ft": 0,
        "away_goals_ft": 0,
        "result_ft": "D",
    }
    with pytest.raises(ValueError):
        normalizer.normalise_row(row, season_code="2324", division="E0")


# ---------------------------------------------------------------------------
# MatchNormalizer.normalise_dataframe
# ---------------------------------------------------------------------------


def test_normalise_dataframe_all_valid(normalizer: MatchNormalizer) -> None:
    df = pd.DataFrame(
        {
            "date": ["12/08/2023", "19/08/2023"],
            "home_team": ["Arsenal", "Chelsea"],
            "away_team": ["Forest", "Liverpool"],
            "home_goals_ft": [2, 1],
            "away_goals_ft": [1, 1],
            "result_ft": ["H", "D"],
        }
    )
    result_df, failed = normalizer.normalise_dataframe(
        df, season_code="2324", division="E0"
    )
    assert failed == 0
    assert len(result_df) == 2
    assert "match_date" in result_df.columns
    assert "competition" in result_df.columns


def test_normalise_dataframe_skips_bad_rows(normalizer: MatchNormalizer) -> None:
    df = pd.DataFrame(
        {
            "date": ["bad-date", "19/08/2023"],
            "home_team": ["A", "Chelsea"],
            "away_team": ["B", "Liverpool"],
            "home_goals_ft": [0, 1],
            "away_goals_ft": [0, 1],
            "result_ft": ["D", "D"],
        }
    )
    result_df, failed = normalizer.normalise_dataframe(
        df, season_code="2324", division="E0"
    )
    assert failed == 1
    assert len(result_df) == 1


def test_normalise_dataframe_all_bad_returns_empty(normalizer: MatchNormalizer) -> None:
    df = pd.DataFrame(
        {
            "date": ["bad"],
            "home_team": ["A"],
            "away_team": ["B"],
            "home_goals_ft": [0],
            "away_goals_ft": [0],
            "result_ft": ["D"],
        }
    )
    result_df, failed = normalizer.normalise_dataframe(
        df, season_code="2324", division="E0"
    )
    assert result_df.empty
    assert failed == 1
