"""Response schema for the teams endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TeamsResponse(BaseModel):
    """Teams of the latest season the server has results for."""

    competition: str = Field(..., examples=["Premier League"])
    season: str = Field(..., description="Season label.", examples=["2026/27"])
    teams: list[str] = Field(..., description="Team names, sorted alphabetically.")
