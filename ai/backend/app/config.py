"""Application configuration loaded from environment / .env file."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Tuned on 2022/23 in docs/reports/draw-handling.md (ADR 011).
DEFAULT_DRAW_POSSIBLE_THRESHOLD = 0.28


class Settings(BaseSettings):
    """Runtime configuration for the Football Intelligence backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Lets LIVE_REFRESH_HOUR=off and RATE_LIMIT_PER_MINUTE=off turn those off.
        env_parse_none_str="off",
    )

    model_path: Path = Path("../ai/models/latest/model.joblib")
    registry_path: Path = Path("../ai/models/registry.json")
    # The original model behind API v1 and unversioned paths (ADR 014).
    v1_model_path: Path = Path("../ai/models/runs/20260630_132617/model.joblib")
    v1_model_version: str = "20260630_132617"
    # Requests per client per minute; `off` turns rate limiting off (ADR 014).
    rate_limit_per_minute: int | None = Field(default=120, ge=1)
    matches_dir: Path = Path("../datasets/processed/football_data")
    datasets_dir: Path = Path("../datasets")
    # Local hour of the daily data refresh (ADR 013); set to `off` to turn it off.
    live_refresh_hour: int | None = Field(default=6, ge=0, le=23)
    # Leagues the API serves (ADR 012); requests naming no league get the default.
    served_competitions: list[str] = [
        "Premier League",
        "Bundesliga",
        "La Liga",
        "Serie A",
        "Ligue 1",
    ]
    default_competition: str = "Premier League"
    draw_possible_threshold: float = DEFAULT_DRAW_POSSIBLE_THRESHOLD
    api_version: str = "0.1.0"
    log_level: str = "INFO"

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"
    assistant_vector_store_path: Path = Path("assistant/vector_store")
    assistant_knowledge_root: Path = Path(".")
    assistant_top_k: int = 5


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the singleton Settings instance (cached after first call)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
