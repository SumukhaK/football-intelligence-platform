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
    return HealthResponse(
        status="ok",
        model_loaded=model_loaded,
        explainability_available=expl_available,
        assistant_available=asst_available,
        version=get_settings().api_version,
    )
