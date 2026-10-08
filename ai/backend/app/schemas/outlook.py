"""Pydantic schemas for GET /teams/{team}/outlook (ADR 023)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class TeamProjectionSchema(BaseModel):
    """One team's projected finish."""

    team: str
    current_points: int = Field(..., ge=0, description="Points so far this season.")
    expected_points: float = Field(..., ge=0.0, description="Mean final points.")
    most_likely_position: int = Field(..., ge=1, description="Modal final position.")
    chance_first: float = Field(..., ge=0.0, le=1.0, description="Chance of the title.")
    chance_top_four: float = Field(
        ..., ge=0.0, le=1.0, description="Chance of a top-four finish."
    )
    chance_bottom_three: float = Field(
        ..., ge=0.0, le=1.0, description="Chance of finishing in the bottom three."
    )


class OutlookPointSchema(BaseModel):
    """The team's chances as they stood on one date, with no later results."""

    as_of: date = Field(..., description="Last day whose results are included.")
    played: int = Field(..., ge=0, description="The team's matches played by then.")
    most_likely_position: int = Field(..., ge=1)
    chance_first: float = Field(..., ge=0.0, le=1.0)
    chance_top_four: float = Field(..., ge=0.0, le=1.0)
    chance_bottom_three: float = Field(..., ge=0.0, le=1.0)


class TeamStrengthSchema(BaseModel):
    """Attack and defence as multiples of a league-average side, like /insights."""

    attack: float = Field(..., gt=0.0, description="Above 1 scores more than average.")
    defence: float = Field(
        ..., gt=0.0, description="Goals conceded; below 1 concedes fewer than average."
    )


class TeamOutlookResponse(BaseModel):
    """A team's projected season finish and how its chances have moved."""

    competition: str
    season: str
    team: str
    as_of: date = Field(..., description="Date of the current projection.")
    model_version: str = Field(
        ..., description="Goals model of the current projection."
    )
    fitted_before: str = Field(
        ..., description="The goals model saw matches before this."
    )
    simulations: int = Field(
        ..., ge=1, description="Runs behind the current projection."
    )
    history_simulations: int = Field(
        ..., ge=1, description="Runs behind each history point."
    )
    projection: TeamProjectionSchema
    strengths: TeamStrengthSchema
    table: list[TeamProjectionSchema] = Field(
        ..., description="The projected league table, highest expected points first."
    )
    history: list[OutlookPointSchema] = Field(
        ..., description="One point before the first match, then one per week played."
    )
