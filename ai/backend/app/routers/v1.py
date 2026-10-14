"""API v1: the Premier League-only contract, served by the July 2026 model (ADR 014).

Clients built against release v1.0.0 keep working unchanged. v1 serves only
the Premier League, answers with the original model (``V1_MODEL_PATH``) and
returns the original response fields. New fields such as ``competition`` and
``draw_possible`` exist only in v2. Server-side features (ADR 008) are
available here too, because the old model uses the same 42 features.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from backend.app.dependencies import (
    FixtureFeatureServiceDep,
    OptionalFixtureFeatureServiceDep,
)
from backend.app.exceptions import ModelNotAvailableError, UnknownCompetitionError
from backend.app.schemas.common import ModelInfoResponse
from backend.app.schemas.explainability import ExplanationResponse
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse
from backend.app.schemas.teams import TeamsResponse
from backend.app.services.explanation_service import ExplanationService
from backend.app.services.fixture_feature_service import resolve_features
from backend.app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)

V1_COMPETITION = "Premier League"
_V2_ONLY_FIELDS = {"competition", "draw_possible"}
_DISPLAY_FIELDS = {"display_name", "display_value"}
_V1_EXPLANATION_EXCLUDE: dict[str, Any] = {
    "competition": True,
    "top_positive_features": {"__all__": _DISPLAY_FIELDS},
    "top_negative_features": {"__all__": _DISPLAY_FIELDS},
    "all_contributions": {"__all__": _DISPLAY_FIELDS},
}

_V1_422 = "Not a Premier League fixture, unknown team, or bad features."

router = APIRouter(tags=["v1 (Premier League, original model)"])


def get_v1_prediction_service(request: Request) -> PredictionService:
    """The original model's prediction service, loaded at startup."""
    service: PredictionService | None = getattr(
        request.app.state, "v1_prediction_service", None
    )
    if service is None:
        raise ModelNotAvailableError(
            "The v1 model is not loaded. Check V1_MODEL_PATH in configuration.",
            component="prediction_model_v1",
        )
    return service


def get_v1_explanation_service(request: Request) -> ExplanationService:
    """The original model's explanation service, loaded at startup."""
    service: ExplanationService | None = getattr(
        request.app.state, "v1_explanation_service", None
    )
    if service is None:
        raise ModelNotAvailableError(
            "The v1 explainer is not loaded. Check V1_MODEL_PATH in configuration.",
            component="explanation",
        )
    return service


V1PredictionDep = Annotated[PredictionService, Depends(get_v1_prediction_service)]
V1ExplanationDep = Annotated[ExplanationService, Depends(get_v1_explanation_service)]


def _premier_league_only(request: PredictionRequest) -> None:
    if request.competition is not None and request.competition != V1_COMPETITION:
        raise UnknownCompetitionError(request.competition, [V1_COMPETITION])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    response_model_exclude=_V2_ONLY_FIELDS,
    summary="Predict a Premier League match (v1)",
    description=(
        "The v1.0.0 contract: Premier League only, answered by the original "
        "model. Use /v2/predict for all five leagues and the current model."
    ),
    responses={
        422: {"description": _V1_422},
        503: {"description": "v1 model or match history not loaded."},
    },
)
def predict_v1(
    request: PredictionRequest,
    service: V1PredictionDep,
    fixtures: OptionalFixtureFeatureServiceDep,
) -> PredictionResponse:
    """Run the original model on a Premier League fixture."""
    _premier_league_only(request)
    features = resolve_features(request, fixtures, V1_COMPETITION)
    logger.info("v1 predict: home=%s away=%s", request.home_team, request.away_team)
    return service.predict(request.model_copy(update={"features": features}))


@router.post(
    "/explain",
    response_model=ExplanationResponse,
    response_model_exclude=_V1_EXPLANATION_EXCLUDE,
    summary="Explain a Premier League prediction (v1)",
    description="SHAP attribution from the original model, in the v1.0.0 format.",
    responses={
        422: {"description": _V1_422},
        503: {"description": "v1 explainer or match history not loaded."},
    },
)
def explain_v1(
    request: PredictionRequest,
    service: V1ExplanationDep,
    fixtures: OptionalFixtureFeatureServiceDep,
) -> ExplanationResponse:
    """Explain the original model's prediction for a Premier League fixture."""
    _premier_league_only(request)
    features = resolve_features(request, fixtures, V1_COMPETITION)
    return service.explain(
        home_team=request.home_team, away_team=request.away_team, features=features
    )


@router.get(
    "/teams",
    response_model=TeamsResponse,
    summary="Premier League teams (v1)",
    responses={503: {"description": "Match history not loaded."}},
)
def teams_v1(service: FixtureFeatureServiceDep) -> TeamsResponse:
    """The Premier League's latest season and teams."""
    return service.teams(V1_COMPETITION)


@router.get(
    "/model",
    response_model=ModelInfoResponse,
    summary="The original model (v1)",
    responses={503: {"description": "Model registry not available."}},
)
def model_v1(request: Request) -> ModelInfoResponse:
    """Registry entry of the model v1 serves."""
    registry = getattr(request.app.state, "registry", None)
    version = getattr(request.app.state, "v1_model_version", None)
    entries = registry.list_versions() if registry is not None else []
    entry = next((e for e in entries if e.version == version), None)
    if entry is None:
        raise ModelNotAvailableError("The v1 model is not in the registry.")
    return ModelInfoResponse(
        model_version=entry.version,
        dataset_version=entry.source_dataset_version,
        training_timestamp=entry.created_at.isoformat(),
        git_commit=entry.git_commit,
        metrics=entry.metrics,
    )
