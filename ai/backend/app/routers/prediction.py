"""Match outcome prediction endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from backend.app.dependencies import (
    OptionalFixtureFeatureServiceDep,
    PredictionServiceDep,
)
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse
from backend.app.services.fixture_feature_service import resolve_features

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prediction"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict match outcome",
    description=(
        "Given the two teams, the server computes the match features from "
        "results before the match date and returns the predicted outcome "
        "(H/D/A), per-class probabilities and the confidence (max probability). "
        "A pre-computed feature vector may be sent instead."
    ),
    responses={
        422: {"description": "Unknown team, or supplied features incomplete."},
        503: {"description": "Model not loaded, or match history not loaded."},
    },
)
def predict(
    request: PredictionRequest,
    service: PredictionServiceDep,
    fixtures: OptionalFixtureFeatureServiceDep,
) -> PredictionResponse:
    """Run the XGBoost model and return a structured prediction."""
    supplied = request.features is not None
    features = resolve_features(request, fixtures)
    logger.info(
        "predict: home=%s away=%s n_features=%d supplied=%s",
        request.home_team,
        request.away_team,
        len(features),
        supplied,
    )
    response = service.predict(request.model_copy(update={"features": features}))
    logger.info(
        "predict: result=%s confidence=%.3f",
        response.predicted_result,
        response.confidence,
    )
    return response
