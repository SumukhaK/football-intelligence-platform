"""Request and response schemas for the prediction endpoint."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Input for POST /predict and POST /explain.

    Send just the two teams and the server computes the match features from
    results played before ``match_date`` (ADR 008). A caller may instead send
    its own pre-computed ``features``; names must match the loaded model's.
    """

    home_team: str = Field(
        ...,
        min_length=1,
        description="Name of the home team.",
        examples=["Arsenal"],
    )
    away_team: str = Field(
        ...,
        min_length=1,
        description="Name of the away team.",
        examples=["Chelsea"],
    )
    competition: str | None = Field(
        default=None,
        description=(
            "League of the fixture, as listed by GET /competitions. "
            "Defaults to the Premier League (ADR 012)."
        ),
        examples=["Bundesliga"],
    )
    features: dict[str, float] | None = Field(
        default=None,
        description=(
            "Optional pre-computed feature vector. When omitted, the server "
            "computes all model features from match history. When given, "
            "every model-required feature must be present."
        ),
        examples=[{"home_elo_before": 1550.0, "away_elo_before": 1480.0}],
    )
    match_date: date | None = Field(
        default=None,
        description=(
            "Date of the fixture; only matches before it are used. "
            "Defaults to today. Ignored when features are supplied."
        ),
        examples=["2026-10-03"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "match_date": "2026-10-03",
            }
        }
    }


class PredictionResponse(BaseModel):
    """Response body for POST /predict."""

    competition: str = Field(
        default="", description="League of the fixture.", examples=["Premier League"]
    )
    home_team: str = Field(..., description="Home team name.")
    away_team: str = Field(..., description="Away team name.")
    predicted_result: str = Field(
        ...,
        description="Predicted outcome: 'H' (home win), 'D' (draw), 'A' (away win).",
        examples=["H"],
    )
    probability_home: float = Field(
        ..., ge=0.0, le=1.0, description="Predicted probability of a home win."
    )
    probability_draw: float = Field(
        ..., ge=0.0, le=1.0, description="Predicted probability of a draw."
    )
    probability_away: float = Field(
        ..., ge=0.0, le=1.0, description="Predicted probability of an away win."
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Maximum probability across all outcomes.",
    )
    draw_possible: bool = Field(
        default=False,
        description=(
            "True when the draw probability is at least the server's draw "
            "threshold (0.28 by default). About 3 in 10 matches are flagged, and "
            "they end level more often than the rest. The predicted_result is "
            "unchanged (ADR 011)."
        ),
    )
    model_version: str = Field(..., description="Version tag of the model used.")
