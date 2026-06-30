"""Application configuration loaded from environment / .env file."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Football Intelligence backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    model_path: Path = Path("../ai/models/latest/model.joblib")
    registry_path: Path = Path("../ai/models/registry.json")
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
