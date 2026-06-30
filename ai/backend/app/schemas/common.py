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
