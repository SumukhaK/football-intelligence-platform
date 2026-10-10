"""Build the services the API serves from, one component at a time.

Each loader raises when its component cannot be built; ``load_component`` in
``startup_telemetry`` turns that into a ``component.load`` event and a None
service, so the component's endpoints answer 503.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

from model_registry.registry import ModelRegistry

if TYPE_CHECKING:
    from assistant.retrieval.vector_store import IndexInfo
    from backend.app.config import Settings
    from backend.app.services.chat_service import ChatService
    from backend.app.services.explanation_service import ExplanationService
    from backend.app.services.fixture_feature_service import FixtureFeatureService
    from backend.app.services.fixtures_service import FixturesService
    from backend.app.services.insights_service import InsightsService
    from backend.app.services.outlook_service import OutlookService
    from backend.app.services.prediction_service import PredictionService
    from backend.app.services.season_service import SeasonService

logger = logging.getLogger(__name__)


def model_versions(registry: ModelRegistry, version: str | None) -> tuple[str, str]:
    """The model and dataset versions to report for a registry entry.

    ``version`` names the entry; None means the latest.
    """
    entries = registry.list_versions()
    if version is None:
        entry = entries[-1] if entries else None
    else:
        entry = next((e for e in entries if e.version == version), None)
    model_version = entry.version if entry else (version or "unknown")
    return model_version, entry.source_dataset_version if entry else "unknown"


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Model file not found at {path}")


def load_prediction(
    path: Path, model_version: str, draw_threshold: float
) -> PredictionService:
    """Prediction service for one model file."""
    from backend.app.services.prediction_service import PredictionService
    from inference.predictor import MatchPredictor

    _require_file(path)
    service = PredictionService(
        MatchPredictor.from_path(path), model_version, draw_threshold
    )
    logger.info("Prediction model loaded: version=%s path=%s", model_version, path)
    return service


def load_explanation(
    path: Path, model_version: str, dataset_version: str
) -> ExplanationService:
    """Explanation service for one model file."""
    from backend.app.services.explanation_service import ExplanationService
    from explainability.services.explanation_service import (
        ExplanationService as AIExplanationService,
    )

    _require_file(path)
    explainer = AIExplanationService(path)
    return ExplanationService(explainer, model_version, dataset_version)


def load_season(directory: Path) -> SeasonService:
    """Match history for the assistant's season tools."""
    from backend.app.services.season_service import SeasonService

    return SeasonService.from_directory(directory)


def load_outlook(directory: Path) -> OutlookService:
    """Match history for team season outlooks."""
    from backend.app.services.outlook_service import OutlookService

    return OutlookService.from_directory(directory)


def load_fixtures(directory: Path) -> FixturesService:
    """The newest upcoming-fixtures dataset."""
    from backend.app.services.fixtures_service import FixturesService

    service = FixturesService.from_directory(directory, date.today)
    logger.info("Fixtures loaded, downloaded at %s", service.updated_at)
    return service


def load_fixture_features(
    directory: Path, competitions: list[str]
) -> FixtureFeatureService:
    """Match history for server-side features."""
    from backend.app.services.fixture_feature_service import FixtureFeatureService
    from inference.fixture_features import FixtureFeatureBuilder

    builder = FixtureFeatureBuilder.from_directory(directory)
    for competition in competitions:
        try:
            season, names = builder.teams(competition)
        except KeyError:
            logger.warning("No match history for %s", competition)
            continue
        logger.info(
            "Match history loaded: %s %s, %d teams", competition, season, len(names)
        )
    return FixtureFeatureService(builder)


def load_insights(directory: Path, competitions: list[str]) -> InsightsService:
    """A goals model per league, fitted from match history."""
    from backend.app.services.insights_service import load_insights_service

    service = load_insights_service(directory, competitions)
    logger.info("Goals models fitted: %s", service.model_versions)
    return service


def load_assistant(settings: Settings, state: Any) -> ChatService:
    """The assistant, with its tools and season router over ``state``."""
    from assistant.prompting.templates import DEFAULT_MIN_RELEVANCE
    from assistant.providers import make_provider
    from assistant.retrieval.vector_store import VectorStore
    from assistant.services.assistant_service import AssistantService
    from backend.app.dependencies import get_served_competitions
    from backend.app.services.assistant_tools import AssistantTools
    from backend.app.services.chat_service import ChatService
    from backend.app.services.season_router import SeasonRouter

    a_cfg = _assistant_settings(settings)
    store = VectorStore.load(settings.assistant_vector_store_path)
    provider = make_provider(a_cfg)
    require_matching_index(store.info, provider.embed_model, a_cfg.ollama_embed_model)
    served = get_served_competitions()
    ai_service = AssistantService(
        embedder=provider.embedder,
        generator=provider.generator,
        store=store,
        model_name=provider.chat_model,
        top_k=settings.assistant_top_k,
        tools=AssistantTools(state, served).tools(),
        router=SeasonRouter(state, served),
        min_relevance=store.info.min_relevance if store.info else DEFAULT_MIN_RELEVANCE,
    )
    logger.info(
        "Assistant uses %s (%s); index has %d chunks.",
        settings.assistant_provider,
        provider.chat_model,
        store.size(),
    )
    return ChatService(ai_service)


def require_matching_index(
    info: IndexInfo | None, embed_model: str, legacy_model: str
) -> None:
    """Refuse an index whose vectors came from a different embedding model.

    An index without ``index.json`` predates it and was built with the local
    default, ``legacy_model``. Mixing embedding spaces makes every retrieval
    score meaningless, so this is an error, not a warning (ADR 025).
    """
    built_with = info.embed_model if info else legacy_model
    if built_with != embed_model:
        raise ValueError(
            f"The index was built with {built_with}, but queries would use "
            f"{embed_model}. Rebuild it, or point ASSISTANT_VECTOR_STORE_PATH "
            "at an index built with that model."
        )


def _assistant_settings(settings: Settings) -> Any:
    from assistant.configuration import AssistantSettings

    # "off" never reaches here: main.py skips loading the assistant.
    return AssistantSettings(
        assistant_provider=(
            "workers_ai" if settings.assistant_provider == "workers_ai" else "ollama"
        ),
        workers_ai_account_id=settings.workers_ai_account_id,
        workers_ai_api_token=settings.workers_ai_api_token,
        workers_ai_chat_model=settings.workers_ai_chat_model,
        workers_ai_embed_model=settings.workers_ai_embed_model,
        workers_ai_timeout_s=settings.workers_ai_timeout_s,
        workers_ai_thinking=settings.workers_ai_thinking,
        ollama_base_url=settings.ollama_base_url,
        ollama_chat_model=settings.ollama_chat_model,
        ollama_embed_model=settings.ollama_embed_model,
        vector_store_path=settings.assistant_vector_store_path,
        knowledge_base_root=settings.assistant_knowledge_root,
        top_k=settings.assistant_top_k,
    )
