"""Schema of one upcoming fixture in the processed fixtures dataset (ADR 015)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class ProcessedFixture(BaseModel):
    """One scheduled league match that has not been played yet."""

    competition: str = Field(..., min_length=1)
    match_date: date = Field(..., description="Date in the league's own time zone.")
    kickoff: datetime | None = Field(
        default=None, description="Kick-off with UTC offset; None until confirmed."
    )
    home_team: str = Field(..., min_length=1)
    away_team: str = Field(..., min_length=1)
    round: str = Field(..., min_length=1, examples=["Matchday 8"])

    @model_validator(mode="after")
    def _teams_differ(self) -> ProcessedFixture:
        """A team never plays itself."""
        if self.home_team == self.away_team:
            raise ValueError(f"{self.home_team} cannot play itself")
        return self

    @model_validator(mode="after")
    def _kickoff_on_match_date(self) -> ProcessedFixture:
        """Kick-off, when known, is on the match date and carries an offset."""
        if self.kickoff is None:
            return self
        if self.kickoff.tzinfo is None:
            raise ValueError("kickoff must carry a UTC offset")
        if self.kickoff.date() != self.match_date:
            raise ValueError("kickoff is not on match_date")
        return self


FIXTURE_COLUMNS: list[str] = list(ProcessedFixture.model_fields)
