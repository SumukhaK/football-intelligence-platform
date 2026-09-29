"""Shared response schemas used across multiple endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Structured error body returned on all 4xx/5xx responses."""

    error: str = Field(..., description="Short error category.")
    detail: str = Field(..., description="Human-readable explanation.")


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str = Field(
        ...,
        description="'ok' when the service is healthy.",
        examples=["ok"],
    )
    model_loaded: bool = Field(
        ..., description="True when the prediction model is available."
    )
    explainability_available: bool = Field(
        ..., description="True when the SHAP explainer is available."
    )
    assistant_available: bool = Field(
        ..., description="True when the RAG assistant is available."
    )
    fixture_features_available: bool = Field(
        default=False,
        description=(
            "True when the server can compute match features from history, "
            "so requests may omit features."
        ),
    )
    insights_available: bool = Field(
        default=False,
        description="True when the goals model is fitted, so POST /insights works.",
    )
    matches_through: str | None = Field(
        default=None,
        description="Date of the latest result the server knows, YYYY-MM-DD.",
        examples=["2026-09-20"],
    )
    last_refresh_at: str | None = Field(
        default=None,
        description="When the daily data refresh last ran (ISO 8601), if it has.",
    )
    last_refresh_error: str | None = Field(
        default=None,
        description="Why the last refresh failed; null when it succeeded.",
    )
    version: str = Field(..., description="API version string.", examples=["0.1.0"])


class ModelInfoResponse(BaseModel):
    """Response body for GET /model."""

    model_version: str = Field(..., description="Registered model version tag.")
    dataset_version: str = Field(
        ..., description="Source dataset version the model was trained on."
    )
    training_timestamp: str = Field(
        ..., description="ISO-8601 timestamp of when the model was registered."
    )
    git_commit: str | None = Field(
        None, description="Git commit hash at training time, if available."
    )
    metrics: dict[str, float] = Field(
        default_factory=dict, description="Evaluation metrics from the training run."
    )
