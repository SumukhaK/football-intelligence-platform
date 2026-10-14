"""FastAPI dependency providers.

All heavyweight objects (model, explainer, registry) are loaded once
during application lifespan and stored in app.state.
These functions extract them and raise 503 if unavailable.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, Request

from backend.app.config import get_settings
from backend.app.consent import CONSENT_VERSION
from backend.app.exceptions import (
    FixtureFeaturesNotAvailableError,
    FixturesNotAvailableError,
    InsightsNotAvailableError,
    ModelNotAvailableError,
    SeasonOutlookNotAvailableError,
)
from backend.app.services.account_service import (
    AccountService,
    ConsentRequiredError,
)
from backend.app.services.account_store import User
from backend.app.services.competitions import ServedCompetitions
from backend.app.services.crest_table import CrestTable
from backend.app.services.explanation_service import ExplanationService
from backend.app.services.fixture_feature_service import FixtureFeatureService
from backend.app.services.fixtures_service import FixturesService
from backend.app.services.insights_service import InsightsService
from backend.app.services.outlook_service import OutlookService
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
            "Prediction model is not loaded. Check MODEL_PATH in configuration.",
            component="prediction_model",
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
            "Explanation service is not loaded. Check MODEL_PATH in configuration.",
            component="explanation",
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
            "Match history is not loaded. Check MATCHES_DIR in configuration.",
            component="match_history",
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
            "Goals model is not fitted. Check MATCHES_DIR in configuration.",
            component="goals_model",
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
            "the daily refresh.",
            component="fixtures",
        )
    return service


def get_outlook_service(request: Request) -> OutlookService:
    """Return the OutlookService loaded at startup or by the daily refresh.

    Raises SeasonOutlookNotAvailableError if no match history is loaded.
    """
    service: OutlookService | None = getattr(request.app.state, "outlook_service", None)
    if service is None:
        raise SeasonOutlookNotAvailableError(
            "Match history is not loaded. Check MATCHES_DIR in configuration.",
            component="season_outlook",
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
OutlookServiceDep = Annotated[OutlookService, Depends(get_outlook_service)]
LeagueEmblemsDep = Annotated[CrestTable, Depends(get_league_emblems)]


def get_account_service(request: Request) -> AccountService:
    """Return the AccountService created with the app (ADR 022)."""
    service: AccountService = request.app.state.account_service
    return service


AccountServiceDep = Annotated[AccountService, Depends(get_account_service)]


def bearer_token(authorization: str | None) -> str | None:
    """The token in an ``Authorization: Bearer <token>`` header, if any."""
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def get_signed_in_user(
    accounts: AccountServiceDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """The user behind the bearer token; 401 or 403 when there is none."""
    return accounts.authenticate(bearer_token(authorization))


SignedInUserDep = Annotated[User, Depends(get_signed_in_user)]


def require_consented_user(user: SignedInUserDep) -> User:
    """The signed-in user, who must have accepted the current notice."""
    if user.consent_version != CONSENT_VERSION:
        raise ConsentRequiredError("Accept the current notice to continue.")
    return user
