"""FastAPI application factory for the Football Intelligence Platform backend."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from functools import partial
from pathlib import Path

from fastapi import FastAPI

from backend.app.config import Settings, get_settings
from backend.app.exceptions import (
    AssistantNotAvailableError,
    FeatureMissingError,
    FixtureFeaturesNotAvailableError,
    FixturesNotAvailableError,
    InsightsNotAvailableError,
    ModelNotAvailableError,
    SeasonOutlookNotAvailableError,
    UnknownCompetitionError,
    UnknownTeamError,
    assistant_not_available_handler,
    auth_error_handler,
    feature_missing_handler,
    fixture_features_not_available_handler,
    fixtures_not_available_handler,
    insights_not_available_handler,
    model_not_available_handler,
    season_outlook_not_available_handler,
    unexpected_error_handler,
    unknown_competition_handler,
    unknown_team_handler,
)
from backend.app.loaders import (
    load_assistant,
    load_explanation,
    load_fixture_features,
    load_fixtures,
    load_insights,
    load_outlook,
    load_prediction,
    load_season,
    model_versions,
)
from backend.app.middleware.rate_limit import RateLimitMiddleware, SlidingWindowLimiter
from backend.app.middleware.request_context import RequestContextMiddleware
from backend.app.routing import include_routers
from backend.app.services.account_service import AccountService, AuthError
from backend.app.services.account_store import JsonAccountStore
from backend.app.startup_telemetry import load_component, log_fallback, log_freshness
from model_registry.registry import ModelRegistry
from shared.telemetry.privacy import hash_ref
from shared.telemetry.setup import configure_logging

logger = logging.getLogger(__name__)
# The `service` field on every JSON log line (telemetry contract section 1).
TELEMETRY_SERVICE = "football-api"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load AI services at startup; release at shutdown."""
    settings = get_settings()
    logger.info("Starting Football Intelligence backend v%s", settings.api_version)

    app.state.prediction_service = None
    app.state.explanation_service = None
    app.state.registry = None
    app.state.chat_service = None
    _load_match_data(app)
    refresh_task = _start_live_refresh(app)

    registry = ModelRegistry(settings.registry_path)
    if settings.model_path.exists():
        app.state.registry = registry
    _load_models(app, settings, registry)
    app.state.chat_service = load_component(
        "assistant", lambda: load_assistant(settings, app.state)
    )

    yield

    if refresh_task is not None:
        refresh_task.cancel()
    logger.info("Shutting down Football Intelligence backend.")


def _load_models(app: FastAPI, settings: Settings, registry: ModelRegistry) -> None:
    """Load the latest model, and the original one that API v1 keeps (ADR 014)."""
    threshold = settings.draw_possible_threshold
    latest, dataset = model_versions(registry, None)
    path = settings.model_path
    app.state.prediction_service = load_component(
        "prediction_model", lambda: load_prediction(path, latest, threshold)
    )
    app.state.explanation_service = load_component(
        "explanation", lambda: load_explanation(path, latest, dataset)
    )
    app.state.v1_model_version = settings.v1_model_version
    v1, v1_dataset = model_versions(registry, settings.v1_model_version)
    v1_path = settings.v1_model_path
    app.state.v1_prediction_service = load_component(
        "prediction_model_v1", lambda: load_prediction(v1_path, v1, threshold)
    )
    # The contract names no separate v1 explainer, so its load is not an event.
    try:
        app.state.v1_explanation_service = load_explanation(v1_path, v1, v1_dataset)
    except Exception as exc:  # noqa: BLE001 — /v1/explain answers 503 instead
        logger.warning("v1 explanation service not loaded: %s", exc)
        app.state.v1_explanation_service = None


def _load_match_data(app: FastAPI) -> None:
    """(Re)build every service that reads the match history."""
    settings = get_settings()
    matches, served = settings.matches_dir, settings.served_competitions
    history = load_component(
        "match_history", lambda: load_fixture_features(matches, served)
    )
    app.state.fixture_feature_service = history
    if history is None:
        log_fallback(
            "server_features",
            "supplied_features_only",
            "match_history_not_loaded",
            "Predictions use request features only",
        )
    app.state.insights_service = load_component(
        "goals_model", lambda: load_insights(matches, served)
    )
    app.state.fixtures_service = load_component(
        "fixtures", lambda: load_fixtures(settings.fixtures_dir)
    )
    app.state.season_service = load_component(
        "season_history", lambda: load_season(matches)
    )
    app.state.outlook_service = load_component(
        "season_outlook", lambda: load_outlook(matches)
    )
    log_freshness(history, served)


def _start_live_refresh(app: FastAPI) -> asyncio.Task[None] | None:
    """Schedule the daily data refresh (ADR 013); None when turned off."""
    settings = get_settings()
    app.state.live_refresh_service = None
    if settings.live_refresh_hour is None:
        logger.info("Daily data refresh is off.")
        return None
    from datetime import datetime

    from backend.app.services.live_refresh_service import LiveRefreshService, is_due
    from inference.fixture_features import find_latest_dataset
    from ingestion.live_refresh import dataset_built_at

    def clock() -> datetime:
        return datetime.now().astimezone()

    service = LiveRefreshService(
        refresh=lambda: _refresh_all(settings.datasets_dir, date.today()),
        reload=lambda: _load_match_data(app),
        clock=clock,
    )
    app.state.live_refresh_service = service
    try:
        built = dataset_built_at(find_latest_dataset(settings.matches_dir))
    except FileNotFoundError:
        built = None
    # Missing fixtures are fetched straight away too (ADR 015).
    due = is_due(built, clock(), settings.live_refresh_hour) or (
        app.state.fixtures_service is None
    )
    logger.info(
        "Daily data refresh at %02d:00; refreshing now: %s",
        settings.live_refresh_hour,
        due,
    )
    return asyncio.create_task(service.run_daily(settings.live_refresh_hour, due))


def _refresh_all(datasets_dir: Path, today: date) -> Path:
    """Refresh results, then fixtures; a fixtures failure only keeps the old ones."""
    from ingestion.fixtures import refresh_fixtures
    from ingestion.live_refresh import refresh_live_dataset

    dataset = refresh_live_dataset(datasets_dir, today)
    try:
        logger.info(
            "Fixtures refreshed: %s", refresh_fixtures(datasets_dir, today).name
        )
    except Exception as exc:  # noqa: BLE001 — keep the old fixtures
        log_fallback(
            "fresh_fixtures",
            "previous_fixtures",
            "fixtures_refresh_failed",
            f"Fixtures refresh failed; keeping the previous fixtures: {exc}",
        )
    return dataset


def _add_exception_handlers(app: FastAPI) -> None:
    """Map each domain error to its structured JSON response."""
    app.add_exception_handler(ModelNotAvailableError, model_not_available_handler)
    app.add_exception_handler(
        AssistantNotAvailableError, assistant_not_available_handler
    )
    app.add_exception_handler(FeatureMissingError, feature_missing_handler)
    app.add_exception_handler(
        FixtureFeaturesNotAvailableError, fixture_features_not_available_handler
    )
    app.add_exception_handler(UnknownTeamError, unknown_team_handler)
    app.add_exception_handler(UnknownCompetitionError, unknown_competition_handler)
    app.add_exception_handler(InsightsNotAvailableError, insights_not_available_handler)
    app.add_exception_handler(FixturesNotAvailableError, fixtures_not_available_handler)
    app.add_exception_handler(
        SeasonOutlookNotAvailableError, season_outlook_not_available_handler
    )
    app.add_exception_handler(AuthError, auth_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)


def create_app() -> FastAPI:
    """Construct and return the FastAPI application."""
    settings = get_settings()
    # Here rather than in lifespan, so uvicorn's startup lines are formatted too.
    configure_logging(
        settings.log_level,
        settings.log_format,
        {
            "service": TELEMETRY_SERVICE,
            "api_version": settings.api_version,
            "revision": settings.revision,
            "gcp_project_id": settings.gcp_project_id,
        },
    )

    app = FastAPI(
        title="Football Intelligence Platform API",
        description=(
            "REST API exposing XGBoost match outcome predictions, "
            "SHAP-driven explanations and goals-model insights for the top "
            "five European leagues."
        ),
        version=settings.api_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    _add_exception_handlers(app)

    app.state.account_service = AccountService(
        JsonAccountStore(settings.accounts_path),
        user_ref=partial(hash_ref, salt=settings.telemetry_salt),
    )
    include_routers(app, settings.auth_required)
    if settings.rate_limit_per_minute is not None:
        app.add_middleware(
            RateLimitMiddleware,
            limiter=SlidingWindowLimiter(settings.rate_limit_per_minute),
            salt=settings.telemetry_salt,
        )
    # Added last so it is the outermost layer and 429s get an ID too.
    app.add_middleware(RequestContextMiddleware)
    return app


app = create_app()
