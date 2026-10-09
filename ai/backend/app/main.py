"""FastAPI application factory for the Football Intelligence Platform backend."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI

from backend.app.config import get_settings
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
from backend.app.middleware.rate_limit import RateLimitMiddleware, SlidingWindowLimiter
from backend.app.middleware.request_context import RequestContextMiddleware
from backend.app.routing import include_routers
from backend.app.services.account_service import AccountService, AuthError
from backend.app.services.account_store import JsonAccountStore
from model_registry.registry import ModelRegistry
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
    app.state.prediction_service, app.state.explanation_service = _load_model(
        settings.model_path, registry, version=None
    )
    # API v1 keeps answering with the original model (ADR 014).
    app.state.v1_model_version = settings.v1_model_version
    app.state.v1_prediction_service, app.state.v1_explanation_service = _load_model(
        settings.v1_model_path, registry, version=settings.v1_model_version
    )

    try:
        from assistant.configuration import AssistantSettings
        from assistant.embeddings.embedder import OllamaEmbedder
        from assistant.generation.generator import OllamaGenerator
        from assistant.retrieval.vector_store import VectorStore
        from backend.app.services.chat_service import ChatService

        a_cfg = AssistantSettings(
            ollama_base_url=settings.ollama_base_url,
            ollama_chat_model=settings.ollama_chat_model,
            ollama_embed_model=settings.ollama_embed_model,
            vector_store_path=settings.assistant_vector_store_path,
            knowledge_base_root=settings.assistant_knowledge_root,
            top_k=settings.assistant_top_k,
        )
        store = VectorStore.load(a_cfg.vector_store_path)
        embedder = OllamaEmbedder(
            model=a_cfg.ollama_embed_model, base_url=a_cfg.ollama_base_url
        )
        generator = OllamaGenerator(
            model=a_cfg.ollama_chat_model,
            base_url=a_cfg.ollama_base_url,
            temperature=a_cfg.temperature,
            max_tokens=a_cfg.max_tokens,
        )
        from assistant.services.assistant_service import AssistantService
        from backend.app.dependencies import get_served_competitions
        from backend.app.services.assistant_tools import AssistantTools
        from backend.app.services.season_router import SeasonRouter

        served = get_served_competitions()
        tools = AssistantTools(app.state, served).tools()
        ai_service = AssistantService(
            embedder=embedder,
            generator=generator,
            store=store,
            model_name=a_cfg.ollama_chat_model,
            top_k=a_cfg.top_k,
            tools=tools,
            router=SeasonRouter(app.state, served),
        )
        app.state.chat_service = ChatService(ai_service)
        logger.info("Assistant service loaded: %d chunks in index.", store.size())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Assistant service not loaded: %s", exc)

    yield

    if refresh_task is not None:
        refresh_task.cancel()
    logger.info("Shutting down Football Intelligence backend.")


def _load_model(
    path: Path, registry: ModelRegistry, version: str | None
) -> tuple[object | None, object | None]:
    """Prediction and explanation services for one model file.

    ``version`` names the registry entry to report; None means the latest.
    Either service is None when it can't be loaded, so its endpoints answer 503.
    """
    if not path.exists():
        logger.warning("Model not found at %s; its endpoints are disabled.", path)
        return None, None
    entries = registry.list_versions()
    if version is None:
        entry = entries[-1] if entries else None
    else:
        entry = next((e for e in entries if e.version == version), None)
    model_version = entry.version if entry else (version or "unknown")
    dataset_version = entry.source_dataset_version if entry else "unknown"
    return (
        _load_prediction(path, model_version),
        _load_explanation(path, model_version, dataset_version),
    )


def _load_prediction(path: Path, model_version: str) -> object | None:
    """Prediction service for one model file; None if it can't be loaded."""
    try:
        from backend.app.services.prediction_service import PredictionService
        from inference.predictor import MatchPredictor

        service = PredictionService(
            MatchPredictor.from_path(path),
            model_version,
            get_settings().draw_possible_threshold,
        )
        logger.info("Prediction model loaded: version=%s path=%s", model_version, path)
        return service
    except Exception as exc:  # noqa: BLE001 — /predict answers 503 instead
        logger.error("Failed to load prediction model %s: %s", path, exc)
        return None


def _load_explanation(
    path: Path, model_version: str, dataset_version: str
) -> object | None:
    """Explanation service for one model file; None if it can't be loaded."""
    try:
        from backend.app.services.explanation_service import ExplanationService
        from explainability.services.explanation_service import (
            ExplanationService as AIExplanationService,
        )

        service = ExplanationService(
            AIExplanationService(path), model_version, dataset_version
        )
        logger.info("Explanation service loaded: version=%s", model_version)
        return service
    except Exception as exc:  # noqa: BLE001 — /explain answers 503 instead
        logger.error("Failed to load explanation service %s: %s", path, exc)
        return None


def _load_match_data(app: FastAPI) -> None:
    """(Re)build every service that reads the match history."""
    settings = get_settings()
    app.state.fixture_feature_service = _load_fixture_features(
        settings.matches_dir, settings.served_competitions
    )
    app.state.insights_service = _load_insights(
        settings.matches_dir, settings.served_competitions
    )
    app.state.fixtures_service = _load_fixtures(settings.fixtures_dir)
    app.state.season_service = _load_season(settings.matches_dir)
    app.state.outlook_service = _load_outlook(settings.matches_dir)


def _load_season(directory: Path) -> object | None:
    """Load match history for the assistant's season tools; None if unavailable."""
    try:
        from backend.app.services.season_service import SeasonService

        return SeasonService.from_directory(directory)
    except Exception as exc:  # noqa: BLE001 — the season tools report it instead
        logger.warning("Season history not loaded from %s: %s", directory, exc)
        return None


def _load_outlook(directory: Path) -> object | None:
    """Load match history for team season outlooks; None if unavailable."""
    try:
        from backend.app.services.outlook_service import OutlookService

        return OutlookService.from_directory(directory)
    except Exception as exc:  # noqa: BLE001 — /teams/{team}/outlook answers 503 instead
        logger.warning("Season outlook history not loaded from %s: %s", directory, exc)
        return None


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
    """Refresh results, then fixtures; a fixtures failure is only logged."""
    from ingestion.fixtures import refresh_fixtures
    from ingestion.live_refresh import refresh_live_dataset

    dataset = refresh_live_dataset(datasets_dir, today)
    try:
        logger.info(
            "Fixtures refreshed: %s", refresh_fixtures(datasets_dir, today).name
        )
    except Exception as exc:  # noqa: BLE001 — keep the old fixtures
        logger.warning("Fixtures refresh failed: %s", exc)
    return dataset


def _load_fixtures(directory: Path) -> object | None:
    """Load the newest upcoming-fixtures dataset; None if there is none."""
    try:
        from backend.app.services.fixtures_service import FixturesService

        service = FixturesService.from_directory(directory, date.today)
        logger.info("Fixtures loaded, downloaded at %s", service.updated_at)
        return service
    except Exception as exc:  # noqa: BLE001 — /fixtures answers 503 instead
        logger.warning("Fixtures not loaded from %s: %s", directory, exc)
        return None


def _load_fixture_features(directory: Path, competitions: list[str]) -> object | None:
    """Load match history for server-side features; None if unavailable."""
    try:
        from backend.app.services.fixture_feature_service import (
            FixtureFeatureService,
        )
        from inference.fixture_features import FixtureFeatureBuilder

        builder = FixtureFeatureBuilder.from_directory(directory)
        for competition in competitions:
            try:
                season, names = builder.teams(competition)
            except KeyError:
                logger.warning("No match history for %s", competition)
                continue
            logger.info(
                "Match history loaded: %s %s, %d teams",
                competition,
                season,
                len(names),
            )
        return FixtureFeatureService(builder)
    except Exception as exc:  # noqa: BLE001 — degrade to supplied features only
        logger.warning("Match history not loaded from %s: %s", directory, exc)
        return None


def _load_insights(directory: Path, competitions: list[str]) -> object | None:
    """Fit a goals model per league from match history; None if that fails."""
    try:
        from backend.app.services.insights_service import load_insights_service

        service = load_insights_service(directory, competitions)
        logger.info("Goals models fitted: %s", service.model_versions)
        return service
    except Exception as exc:  # noqa: BLE001 — /insights answers 503 instead
        logger.warning("Goals model not fitted from %s: %s", directory, exc)
        return None


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

    app.state.account_service = AccountService(JsonAccountStore(settings.accounts_path))
    include_routers(app, settings.auth_required)
    if settings.rate_limit_per_minute is not None:
        app.add_middleware(
            RateLimitMiddleware,
            limiter=SlidingWindowLimiter(settings.rate_limit_per_minute),
        )
    # Added last so it is the outermost layer and 429s get an ID too.
    app.add_middleware(RequestContextMiddleware)
    return app


app = create_app()
