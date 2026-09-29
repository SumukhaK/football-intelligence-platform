"""Request and response schemas for the goals insights endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InsightsRequest(BaseModel):
    """Input for POST /insights: the two teams."""

    home_team: str = Field(
        ..., min_length=1, description="Name of the home team.", examples=["Arsenal"]
    )
    away_team: str = Field(
        ..., min_length=1, description="Name of the away team.", examples=["Chelsea"]
    )
    competition: str | None = Field(
        default=None,
        description=(
            "League of the fixture, as listed by GET /competitions. "
            "Defaults to the Premier League (ADR 012)."
        ),
        examples=["Bundesliga"],
    )


class ExpectedGoals(BaseModel):
    """Mean goals for each side."""

    home: float = Field(..., ge=0.0, description="Expected home goals.")
    away: float = Field(..., ge=0.0, description="Expected away goals.")


class ScoreProbabilitySchema(BaseModel):
    """One scoreline and its probability."""

    home: int = Field(..., ge=0, description="Home goals.")
    away: int = Field(..., ge=0, description="Away goals.")
    probability: float = Field(..., ge=0.0, le=1.0)


class GoalMarketsSchema(BaseModel):
    """Probabilities of common goal events."""

    btts: float = Field(..., ge=0.0, le=1.0, description="Both teams score.")
    over_1_5: float = Field(..., ge=0.0, le=1.0, description="Two or more goals.")
    over_2_5: float = Field(..., ge=0.0, le=1.0, description="Three or more goals.")
    over_3_5: float = Field(..., ge=0.0, le=1.0, description="Four or more goals.")
    home_clean_sheet: float = Field(
        ..., ge=0.0, le=1.0, description="The away side does not score."
    )
    away_clean_sheet: float = Field(
        ..., ge=0.0, le=1.0, description="The home side does not score."
    )


class OutcomeSchema(BaseModel):
    """Home/draw/away probabilities implied by the goals model."""

    home: float = Field(..., ge=0.0, le=1.0)
    draw: float = Field(..., ge=0.0, le=1.0)
    away: float = Field(..., ge=0.0, le=1.0)


class StrengthsSchema(BaseModel):
    """Goals scored and conceded as multiples of a league-average side."""

    home_attack: float = Field(..., gt=0.0, description="Above 1 scores more.")
    home_defence: float = Field(..., gt=0.0, description="Below 1 concedes fewer.")
    away_attack: float = Field(..., gt=0.0, description="Above 1 scores more.")
    away_defence: float = Field(..., gt=0.0, description="Below 1 concedes fewer.")


class InsightsResponse(BaseModel):
    """Response body for POST /insights."""

    competition: str = Field(
        default="", description="League of the fixture.", examples=["Premier League"]
    )
    home_team: str
    away_team: str
    model_version: str = Field(
        ..., description="Goals-model version: 'dc-' plus the fit date."
    )
    fitted_before: str = Field(
        ..., description="The model was fitted on matches before this date."
    )
    expected_goals: ExpectedGoals
    top_scores: list[ScoreProbabilitySchema] = Field(
        ..., description="The five most likely scores, most likely first."
    )
    markets: GoalMarketsSchema
    outcome: OutcomeSchema = Field(
        ...,
        description=(
            "For reference only; the headline pick comes from POST /predict "
            "(ADR 009)."
        ),
    )
    strengths: StrengthsSchema
    reasons: list[str] = Field(
        ..., description="Up to three plain-language reasons, strongest first."
    )
