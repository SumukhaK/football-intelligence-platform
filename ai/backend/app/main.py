"""FastAPI application factory for the Football Intelligence Platform backend."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.config import get_settings
from backend.app.exceptions import (
    FeatureMissingError,
    ModelNotAvailableError,
    feature_missing_handler,
    model_not_available_handler,
    unexpected_error_handler,
)
from backend.app.routers import explainability, health, model, prediction

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

    if settings.model_path.exists():
        try:
            from backend.app.services.prediction_service import PredictionService
            from inference.predictor import MatchPredictor
            from model_registry.registry import ModelRegistry

            registry = ModelRegistry(settings.registry_path)
            entry = registry.latest() if settings.registry_path.exists() else None
            model_version = entry.version if entry else "unknown"

            predictor = MatchPredictor.from_path(settings.model_path)
            app.state.prediction_service = PredictionService(predictor, model_version)
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

    yield

    logger.info("Shutting down Football Intelligence backend.")


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
    app.add_exception_handler(FeatureMissingError, feature_missing_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)

    app.include_router(health.router)
    app.include_router(model.router)
    app.include_router(prediction.router)
    app.include_router(explainability.router)

    return app


app = create_app()
