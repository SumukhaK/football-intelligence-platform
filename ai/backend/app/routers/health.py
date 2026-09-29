"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

from backend.app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Returns the current health status of the API, "
        "whether the prediction model is loaded, "
        "and whether SHAP explanations are available."
    ),
)
def health(request: Request) -> HealthResponse:
    """Return API health, model availability, and version."""
    from backend.app.config import get_settings

    model_loaded = getattr(request.app.state, "prediction_service", None) is not None
    expl_available = getattr(request.app.state, "explanation_service", None) is not None
    asst_available = getattr(request.app.state, "chat_service", None) is not None
    fixture_service = getattr(request.app.state, "fixture_feature_service", None)
    insights = getattr(request.app.state, "insights_service", None) is not None
    refresher = getattr(request.app.state, "live_refresh_service", None)
    outcome = refresher.last_outcome if refresher is not None else None
    return HealthResponse(
        status="ok",
        model_loaded=model_loaded,
        explainability_available=expl_available,
        assistant_available=asst_available,
        fixture_features_available=fixture_service is not None,
        insights_available=insights,
        matches_through=(
            fixture_service.matches_through() if fixture_service is not None else None
        ),
        last_refresh_at=outcome.attempted_at.isoformat() if outcome else None,
        last_refresh_error=outcome.error if outcome else None,
        version=get_settings().api_version,
    )
