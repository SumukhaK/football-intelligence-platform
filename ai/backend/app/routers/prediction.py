"""Match outcome prediction endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from backend.app.dependencies import PredictionServiceDep
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prediction"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict match outcome",
    description=(
        "Given a pre-computed feature vector for a match, "
        "returns the predicted outcome (H/D/A), per-class probabilities, "
        "and the confidence score (max probability)."
    ),
    responses={
        422: {"description": "Missing required feature columns."},
        503: {"description": "Prediction model not loaded."},
    },
)
def predict(
    request: PredictionRequest,
    service: PredictionServiceDep,
) -> PredictionResponse:
    """Run the XGBoost model and return a structured prediction."""
    logger.info(
        "predict: home=%s away=%s n_features=%d",
        request.home_team,
        request.away_team,
        len(request.features),
    )
    response = service.predict(request)
    logger.info(
        "predict: result=%s confidence=%.3f",
        response.predicted_result,
        response.confidence,
    )
    return response
