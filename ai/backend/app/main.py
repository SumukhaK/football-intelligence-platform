"""FastAPI application factory for the Football Intelligence Platform backend."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from backend.app.config import get_settings
from backend.app.exceptions import (
    AssistantNotAvailableError,
    FeatureMissingError,
    FixtureFeaturesNotAvailableError,
    InsightsNotAvailableError,
    ModelNotAvailableError,
    UnknownTeamError,
    assistant_not_available_handler,
    feature_missing_handler,
    fixture_features_not_available_handler,
    insights_not_available_handler,
    model_not_available_handler,
    unexpected_error_handler,
    unknown_team_handler,
)
from backend.app.routers import (
    assistant,
    explainability,
    health,
    insights,
    model,
    prediction,
    teams,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load AI services at startup; release at shutdown."""
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    logger.info("Starting Football Intelligence backend v%s", settings.api_version)

    app.state.prediction_service = None
    app.state.explanation_service = None
    app.state.registry = None
    app.state.chat_service = None
    _load_match_data(app)
    refresh_task = _start_live_refresh(app)

    if settings.model_path.exists():
        try:
            from backend.app.services.prediction_service import PredictionService
            from inference.predictor import MatchPredictor
            from model_registry.registry import ModelRegistry

            registry = ModelRegistry(settings.registry_path)
            entry = registry.latest() if settings.registry_path.exists() else None
            model_version = entry.version if entry else "unknown"

            predictor = MatchPredictor.from_path(settings.model_path)
            app.state.prediction_service = PredictionService(
                predictor, model_version, settings.draw_possible_threshold
            )
            app.state.registry = registry

            logger.info(
                "Prediction model loaded: version=%s path=%s",
                model_version,
                settings.model_path,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load prediction model: %s", exc)
    else:
        logger.warning(
            "Model not found at %s — prediction disabled.", settings.model_path
        )

    if settings.model_path.exists():
        try:
            from backend.app.services.explanation_service import ExplanationService
            from explainability.services.explanation_service import (
                ExplanationService as AIExplanationService,
            )
            from model_registry.registry import ModelRegistry

            registry_for_expl = ModelRegistry(settings.registry_path)
            entry_e = (
                registry_for_expl.latest() if settings.registry_path.exists() else None
            )
            mv = entry_e.version if entry_e else "unknown"
            dv = entry_e.source_dataset_version if entry_e else "unknown"

            ai_svc = AIExplanationService(settings.model_path)
            app.state.explanation_service = ExplanationService(ai_svc, mv, dv)

            logger.info("Explanation service loaded.")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load explanation service: %s", exc)

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

        ai_service = AssistantService(
            embedder=embedder,
            generator=generator,
            store=store,
            model_name=a_cfg.ollama_chat_model,
            top_k=a_cfg.top_k,
        )
        app.state.chat_service = ChatService(ai_service)
        logger.info("Assistant service loaded: %d chunks in index.", store.size())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Assistant service not loaded: %s", exc)

    yield

    if refresh_task is not None:
        refresh_task.cancel()
    logger.info("Shutting down Football Intelligence backend.")


def _load_match_data(app: FastAPI) -> None:
    """(Re)build every service that reads the match history."""
    settings = get_settings()
    app.state.fixture_feature_service = _load_fixture_features(
        settings.matches_dir, settings.served_competition
    )
    app.state.insights_service = _load_insights(
        settings.matches_dir, settings.served_competition
    )


def _start_live_refresh(app: FastAPI) -> asyncio.Task[None] | None:
    """Schedule the daily data refresh (ADR 013); None when turned off."""
    settings = get_settings()
    app.state.live_refresh_service = None
    if settings.live_refresh_hour is None:
        logger.info("Daily data refresh is off.")
        return None
    from datetime import date, datetime

    from backend.app.services.live_refresh_service import LiveRefreshService, is_due
    from inference.fixture_features import find_latest_dataset
    from ingestion.live_refresh import dataset_built_at, refresh_live_dataset

    def clock() -> datetime:
        return datetime.now().astimezone()

    service = LiveRefreshService(
        refresh=lambda: refresh_live_dataset(settings.datasets_dir, date.today()),
        reload=lambda: _load_match_data(app),
        clock=clock,
    )
    app.state.live_refresh_service = service
    try:
        built = dataset_built_at(find_latest_dataset(settings.matches_dir))
    except FileNotFoundError:
        built = None
    due = is_due(built, clock(), settings.live_refresh_hour)
    logger.info(
        "Daily data refresh at %02d:00; refreshing now: %s",
        settings.live_refresh_hour,
        due,
    )
    return asyncio.create_task(service.run_daily(settings.live_refresh_hour, due))


def _load_fixture_features(directory: Path, competition: str) -> object | None:
    """Load match history for server-side features; None if unavailable."""
    try:
        from backend.app.services.fixture_feature_service import (
            FixtureFeatureService,
        )
        from inference.fixture_features import FixtureFeatureBuilder

        builder = FixtureFeatureBuilder.from_directory(directory)
        season, names = builder.teams(competition)
        logger.info(
            "Match history loaded: %s %s, %d teams", competition, season, len(names)
        )
        return FixtureFeatureService(builder, competition)
    except Exception as exc:  # noqa: BLE001 — degrade to supplied features only
        logger.warning("Match history not loaded from %s: %s", directory, exc)
        return None


def _load_insights(directory: Path, competition: str) -> object | None:
    """Fit the goals model from match history; None if that fails."""
    try:
        from backend.app.services.insights_service import load_insights_service

        service = load_insights_service(directory, competition)
        logger.info("Goals model fitted: %s", service.model_version)
        return service
    except Exception as exc:  # noqa: BLE001 — /insights answers 503 instead
        logger.warning("Goals model not fitted from %s: %s", directory, exc)
        return None


def create_app() -> FastAPI:
    """Construct and return the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Football Intelligence Platform API",
        description=(
            "REST API exposing XGBoost match outcome predictions and "
            "SHAP-driven feature explanations for Premier League matches."
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
    app.add_exception_handler(InsightsNotAvailableError, insights_not_available_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)

    app.include_router(health.router)
    app.include_router(model.router)
    app.include_router(prediction.router)
    app.include_router(explainability.router)
    app.include_router(teams.router)
    app.include_router(insights.router)
    app.include_router(assistant.router)

    return app


app = create_app()
