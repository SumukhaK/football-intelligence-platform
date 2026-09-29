"""Response schema for the competitions endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompetitionSummary(BaseModel):
    """One served league and how current its data is."""

    name: str = Field(..., examples=["Bundesliga"])
    season: str = Field(..., description="Latest season held.", examples=["2026/27"])
    team_count: int = Field(..., ge=0, description="Teams in that season.")
    matches_through: str = Field(
        ...,
        description="Date of the latest result, YYYY-MM-DD.",
        examples=["2026-09-20"],
    )
    insights_available: bool = Field(
        ..., description="True when the goals model is fitted for this league."
    )


class CompetitionsResponse(BaseModel):
    """Response body for GET /competitions."""

    default: str = Field(
        ...,
        description="League used when a request names none.",
        examples=["Premier League"],
    )
    competitions: list[CompetitionSummary]
