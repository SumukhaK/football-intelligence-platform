"""Response schema for the fixtures endpoint (ADR 015)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class Fixture(BaseModel):
    """One upcoming league match."""

    match_date: date = Field(..., description="Date in the league's time zone.")
    kickoff: datetime | None = Field(
        default=None,
        description="Kick-off with UTC offset; null until the league confirms it.",
        examples=["2026-10-10T12:30:00+01:00"],
    )
    home_team: str = Field(..., examples=["Arsenal"])
    away_team: str = Field(..., examples=["Leeds"])
    round: str = Field(..., examples=["Matchday 6"])


class FixturesResponse(BaseModel):
    """A league's fixtures from today on, earliest first."""

    competition: str = Field(..., examples=["Premier League"])
    fixtures: list[Fixture]
    updated_at: datetime | None = Field(
        default=None, description="When the schedule was last downloaded (UTC)."
    )
