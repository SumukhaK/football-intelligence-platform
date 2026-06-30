"""Canonical Pydantic schemas for raw and processed match data.

``RawMatch`` mirrors the platform-standard column names produced by
``FootballDataProvider.normalise_columns()``.

``ProcessedMatch`` is the canonical downstream schema consumed by the
modelling and retrieval layers.

``MatchNormalizer`` converts a normalised DataFrame into canonical records.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, Field

DIVISION_TO_COMPETITION: dict[str, str] = {
    "E0": "Premier League",
    "E1": "Championship",
    "E2": "League One",
    "E3": "League Two",
    "EC": "Conference National",
}


def parse_match_date(raw: str) -> date:
    """Parse a date string from football-data.co.uk into a ``date``.

    Handles both DD/MM/YYYY (older seasons) and DD/MM/YY (recent seasons).
    """
    raw = raw.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {raw!r}")


def season_label(season_code: str) -> str:
    """Convert a 4-char season code to a human-readable label.

    Example: ``"2324"`` → ``"2023/24"``.
    """
    if len(season_code) != 4 or not season_code.isdigit():
        raise ValueError(f"Invalid season code: {season_code!r}")
    return f"20{season_code[:2]}/{season_code[2:]}"


class RawMatch(BaseModel):
    """Platform-normalised match row from football-data.co.uk.

    Fields mirror the column names produced by
    ``FootballDataProvider.normalise_columns()``.
    """

    model_config = {"frozen": True}

    date: str
    home_team: str
    away_team: str
    home_goals_ft: int
    away_goals_ft: int
    result_ft: Literal["H", "D", "A"]

    time: str | None = None
    division: str | None = None
    referee: str | None = None

    home_goals_ht: int | None = None
    away_goals_ht: int | None = None
    result_ht: str | None = None

    home_shots: int | None = None
    away_shots: int | None = None
    home_shots_on_target: int | None = None
    away_shots_on_target: int | None = None

    home_fouls: int | None = None
    away_fouls: int | None = None
    home_corners: int | None = None
    away_corners: int | None = None
    home_yellow_cards: int | None = None
    away_yellow_cards: int | None = None
    home_red_cards: int | None = None
    away_red_cards: int | None = None

    odds_b365_home: float | None = None
    odds_b365_draw: float | None = None
    odds_b365_away: float | None = None


class ProcessedMatch(BaseModel):
    """Canonical match schema for downstream modelling and retrieval."""

    model_config = {"frozen": True}

    match_date: date
    season: str
    competition: str
    home_team: str
    away_team: str
    full_time_home_goals: int = Field(ge=0)
    full_time_away_goals: int = Field(ge=0)
    result: Literal["H", "D", "A"]

    half_time_home_goals: int | None = Field(default=None, ge=0)
    half_time_away_goals: int | None = Field(default=None, ge=0)

    home_shots: int | None = Field(default=None, ge=0)
    away_shots: int | None = Field(default=None, ge=0)
    home_shots_on_target: int | None = Field(default=None, ge=0)
    away_shots_on_target: int | None = Field(default=None, ge=0)

    home_fouls: int | None = Field(default=None, ge=0)
    away_fouls: int | None = Field(default=None, ge=0)
    home_corners: int | None = Field(default=None, ge=0)
    away_corners: int | None = Field(default=None, ge=0)

    home_yellow_cards: int | None = Field(default=None, ge=0)
    away_yellow_cards: int | None = Field(default=None, ge=0)
    home_red_cards: int | None = Field(default=None, ge=0)
    away_red_cards: int | None = Field(default=None, ge=0)

    home_odds: float | None = Field(default=None, gt=0)
    draw_odds: float | None = Field(default=None, gt=0)
    away_odds: float | None = Field(default=None, gt=0)


def _int_or_none(val: Any) -> int | None:
    """Return int if val is not NaN/None, else None."""
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return int(val)


def _float_or_none(val: Any) -> float | None:
    """Return float if val is not NaN/None, else None."""
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return float(val)


class MatchNormalizer:
    """Converts a normalised DataFrame to canonical ``ProcessedMatch`` records."""

    def normalise_row(
        self,
        row: dict[str, Any],
        *,
        season_code: str,
        division: str,
    ) -> ProcessedMatch:
        """Map one normalised row dict to a ``ProcessedMatch``.

        Raises ``ValueError`` if required fields are missing or unparseable.
        """
        competition = DIVISION_TO_COMPETITION.get(division, division)
        return ProcessedMatch(
            match_date=parse_match_date(str(row["date"])),
            season=season_label(season_code),
            competition=competition,
            home_team=str(row["home_team"]),
            away_team=str(row["away_team"]),
            full_time_home_goals=int(row["home_goals_ft"]),
            full_time_away_goals=int(row["away_goals_ft"]),
            result=row["result_ft"],
            half_time_home_goals=_int_or_none(row.get("home_goals_ht")),
            half_time_away_goals=_int_or_none(row.get("away_goals_ht")),
            home_shots=_int_or_none(row.get("home_shots")),
            away_shots=_int_or_none(row.get("away_shots")),
            home_shots_on_target=_int_or_none(row.get("home_shots_on_target")),
            away_shots_on_target=_int_or_none(row.get("away_shots_on_target")),
            home_fouls=_int_or_none(row.get("home_fouls")),
            away_fouls=_int_or_none(row.get("away_fouls")),
            home_corners=_int_or_none(row.get("home_corners")),
            away_corners=_int_or_none(row.get("away_corners")),
            home_yellow_cards=_int_or_none(row.get("home_yellow_cards")),
            away_yellow_cards=_int_or_none(row.get("away_yellow_cards")),
            home_red_cards=_int_or_none(row.get("home_red_cards")),
            away_red_cards=_int_or_none(row.get("away_red_cards")),
            home_odds=_float_or_none(row.get("odds_b365_home")),
            draw_odds=_float_or_none(row.get("odds_b365_draw")),
            away_odds=_float_or_none(row.get("odds_b365_away")),
        )

    def normalise_dataframe(
        self,
        df: pd.DataFrame,
        *,
        season_code: str,
        division: str,
    ) -> tuple[pd.DataFrame, int]:
        """Convert a normalised DataFrame to a canonical ``ProcessedMatch`` DataFrame.

        Returns ``(canonical_df, failed_count)``. Rows that fail Pydantic
        validation or date parsing are skipped and counted as failures.
        """
        matches: list[ProcessedMatch] = []
        failed = 0
        for _, row in df.iterrows():
            try:
                row_dict: dict[str, Any] = {str(k): v for k, v in row.to_dict().items()}
                matches.append(
                    self.normalise_row(
                        row_dict, season_code=season_code, division=division
                    )
                )
            except (ValueError, KeyError, TypeError):
                failed += 1

        if not matches:
            return pd.DataFrame(), failed

        return pd.DataFrame([m.model_dump() for m in matches]), failed
