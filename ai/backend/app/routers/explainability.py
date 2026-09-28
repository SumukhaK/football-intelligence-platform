"""SHAP explainability endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from backend.app.dependencies import (
    ExplanationServiceDep,
    OptionalFixtureFeatureServiceDep,
)
from backend.app.schemas.explainability import ExplanationResponse
from backend.app.schemas.prediction import PredictionRequest
from backend.app.services.fixture_feature_service import resolve_features

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Explainability"])


@router.post(
    "/explain",
    response_model=ExplanationResponse,
    summary="Explain match prediction with SHAP",
    description=(
        "Given the two teams (or a pre-computed feature vector), "
        "returns the predicted outcome together with SHAP feature attributions: "
        "top positive contributors, top negative contributors, "
        "and the full contribution list sorted by magnitude."
    ),
    responses={
        422: {"description": "Unknown team, or supplied features incomplete."},
        503: {"description": "Explainer not loaded, or match history not loaded."},
    },
)
def explain(
    request: PredictionRequest,
    service: ExplanationServiceDep,
    fixtures: OptionalFixtureFeatureServiceDep,
) -> ExplanationResponse:
    """Compute SHAP values and return a structured explanation."""
    features = resolve_features(request, fixtures)
    logger.info(
        "explain: home=%s away=%s n_features=%d",
        request.home_team,
        request.away_team,
        len(features),
    )
    response = service.explain(
        home_team=request.home_team,
        away_team=request.away_team,
        features=features,
    )
    logger.info(
        "explain: result=%s confidence=%.3f n_contributions=%d",
        response.predicted_result,
        response.confidence,
        len(response.all_contributions),
    )
    return response
