"""Request and response schemas for the prediction endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Input for POST /predict and POST /explain.

    The caller must supply the pre-computed feature vector for the match.
    Feature names must match those expected by the loaded model.
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
    features: dict[str, float] = Field(
        ...,
        description=(
            "Pre-computed match feature vector. "
            "Keys are feature names; values are numeric feature values. "
            "All model-required features must be present."
        ),
        examples=[{"home_elo": 1550.0, "away_elo": 1480.0, "elo_diff": 70.0}],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "features": {
                    "home_elo": 1550.0,
                    "away_elo": 1480.0,
                    "elo_diff": 70.0,
                    "home_form_wins_last5": 0.6,
                    "away_form_wins_last5": 0.4,
                },
            }
        }
    }


class PredictionResponse(BaseModel):
    """Response body for POST /predict."""

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
    model_version: str = Field(..., description="Version tag of the model used.")
