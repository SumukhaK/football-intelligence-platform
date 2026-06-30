"""FastAPI dependency providers.

All heavyweight objects (model, explainer, registry) are loaded once
during application lifespan and stored in app.state.
These functions extract them and raise 503 if unavailable.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from backend.app.exceptions import ModelNotAvailableError
from backend.app.services.explanation_service import ExplanationService
from backend.app.services.prediction_service import PredictionService


def get_prediction_service(request: Request) -> PredictionService:
    """Return the PredictionService loaded at startup.

    Raises ModelNotAvailableError if the model was not successfully loaded.
    """
    service: PredictionService | None = getattr(
        request.app.state, "prediction_service", None
    )
    if service is None:
        raise ModelNotAvailableError(
            "Prediction model is not loaded. Check MODEL_PATH in configuration."
        )
    return service


def get_explanation_service(request: Request) -> ExplanationService:
    """Return the ExplanationService loaded at startup.

    Raises ModelNotAvailableError if the explainer was not successfully loaded.
    """
    service: ExplanationService | None = getattr(
        request.app.state, "explanation_service", None
    )
    if service is None:
        raise ModelNotAvailableError(
            "Explanation service is not loaded. Check MODEL_PATH in configuration."
        )
    return service


PredictionServiceDep = Annotated[PredictionService, Depends(get_prediction_service)]
ExplanationServiceDep = Annotated[ExplanationService, Depends(get_explanation_service)]
