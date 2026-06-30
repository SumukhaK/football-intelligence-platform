"""Request and response schemas for the explainability endpoint."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FeatureContributionSchema(BaseModel):
    """SHAP contribution of a single feature."""

    feature_name: str = Field(..., description="Feature identifier.")
    feature_value: float = Field(..., description="Input value of this feature.")
    shap_value: float = Field(
        ..., description="SHAP value (positive = pushes toward predicted class)."
    )


class ExplanationResponse(BaseModel):
    """Response body for POST /explain."""

    home_team: str = Field(..., description="Home team name.")
    away_team: str = Field(..., description="Away team name.")
    predicted_result: str = Field(
        ...,
        description="Predicted outcome: 'H', 'D', or 'A'.",
        examples=["H"],
    )
    probability_home: float = Field(..., ge=0.0, le=1.0)
    probability_draw: float = Field(..., ge=0.0, le=1.0)
    probability_away: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Max probability across outcomes."
    )
    top_positive_features: list[FeatureContributionSchema] = Field(
        ...,
        description=(
            "Features that most strongly pushed the prediction "
            "toward the predicted outcome (positive SHAP, sorted by magnitude)."
        ),
    )
    top_negative_features: list[FeatureContributionSchema] = Field(
        ...,
        description=(
            "Features that most strongly pushed against the predicted outcome "
            "(negative SHAP, sorted by magnitude)."
        ),
    )
    all_contributions: list[FeatureContributionSchema] = Field(
        ...,
        description="Full SHAP contributions for all features, sorted by magnitude.",
    )
    model_version: str = Field(..., description="Version tag of the model used.")
    feature_version: str = Field(
        ..., description="Feature pipeline version, if available."
    )
    dataset_version: str = Field(
        ..., description="Source dataset version the model was trained on."
    )
    explanation_timestamp: datetime = Field(
        ..., description="UTC timestamp when this explanation was generated."
    )
