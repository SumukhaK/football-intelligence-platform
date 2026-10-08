"""FastAPI dependency providers.

All heavyweight objects (model, explainer, registry) are loaded once
during application lifespan and stored in app.state.
These functions extract them and raise 503 if unavailable.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from backend.app.config import get_settings
from backend.app.exceptions import (
    FixtureFeaturesNotAvailableError,
    FixturesNotAvailableError,
    InsightsNotAvailableError,
    ModelNotAvailableError,
)
from backend.app.services.competitions import ServedCompetitions
from backend.app.services.crest_table import CrestTable
from backend.app.services.explanation_service import ExplanationService
from backend.app.services.fixture_feature_service import FixtureFeatureService
from backend.app.services.fixtures_service import FixturesService
from backend.app.services.insights_service import InsightsService
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


def get_optional_fixture_feature_service(
    request: Request,
) -> FixtureFeatureService | None:
    """Return the FixtureFeatureService, or None when history is not loaded."""
    service: FixtureFeatureService | None = getattr(
        request.app.state, "fixture_feature_service", None
    )
    return service


def get_fixture_feature_service(request: Request) -> FixtureFeatureService:
    """Return the FixtureFeatureService loaded at startup.

    Raises FixtureFeaturesNotAvailableError if match history was not loaded.
    """
    service = get_optional_fixture_feature_service(request)
    if service is None:
        raise FixtureFeaturesNotAvailableError(
            "Match history is not loaded. Check MATCHES_DIR in configuration."
        )
    return service


def get_insights_service(request: Request) -> InsightsService:
    """Return the InsightsService fitted at startup.

    Raises InsightsNotAvailableError if the goals model could not be fitted.
    """
    service: InsightsService | None = getattr(
        request.app.state, "insights_service", None
    )
    if service is None:
        raise InsightsNotAvailableError(
            "Goals model is not fitted. Check MATCHES_DIR in configuration."
        )
    return service


def get_served_competitions() -> ServedCompetitions:
    """Return the served leagues and the default, from configuration."""
    settings = get_settings()
    return ServedCompetitions(
        tuple(settings.served_competitions), settings.default_competition
    )


def get_optional_insights_service(request: Request) -> InsightsService | None:
    """Return the InsightsService, or None when no goals model is fitted."""
    service: InsightsService | None = getattr(
        request.app.state, "insights_service", None
    )
    return service


def get_fixtures_service(request: Request) -> FixturesService:
    """Return the FixturesService loaded at startup or by the daily refresh.

    Raises FixturesNotAvailableError if no fixtures dataset is loaded.
    """
    service: FixturesService | None = getattr(
        request.app.state, "fixtures_service", None
    )
    if service is None:
        raise FixturesNotAvailableError(
            "No fixtures loaded yet. Run scripts.refresh_fixtures or wait for "
            "the daily refresh."
        )
    return service


@lru_cache(maxsize=1)
def get_team_crests() -> CrestTable:
    """Return the team crest table, loaded on first use (ADR 020)."""
    return CrestTable.from_csv(get_settings().team_crests_path)


@lru_cache(maxsize=1)
def get_league_emblems() -> CrestTable:
    """Return the league emblem table, loaded on first use (ADR 020)."""
    return CrestTable.from_csv(get_settings().league_emblems_path)


PredictionServiceDep = Annotated[PredictionService, Depends(get_prediction_service)]
ExplanationServiceDep = Annotated[ExplanationService, Depends(get_explanation_service)]
OptionalFixtureFeatureServiceDep = Annotated[
    FixtureFeatureService | None, Depends(get_optional_fixture_feature_service)
]
FixtureFeatureServiceDep = Annotated[
    FixtureFeatureService, Depends(get_fixture_feature_service)
]
InsightsServiceDep = Annotated[InsightsService, Depends(get_insights_service)]
ServedCompetitionsDep = Annotated[ServedCompetitions, Depends(get_served_competitions)]
OptionalInsightsServiceDep = Annotated[
    InsightsService | None, Depends(get_optional_insights_service)
]
FixturesServiceDep = Annotated[FixturesService, Depends(get_fixtures_service)]
TeamCrestsDep = Annotated[CrestTable, Depends(get_team_crests)]
LeagueEmblemsDep = Annotated[CrestTable, Depends(get_league_emblems)]
