"""Assistant configuration loaded from environment variables or .env file."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AssistantSettings(BaseSettings):
    """Runtime configuration for the Football Intelligence Assistant."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"

    vector_store_path: Path = Path("assistant/vector_store")
    knowledge_base_root: Path = Path(".")

    top_k: int = 5
    max_tokens: int = 1024
    temperature: float = 0.1
    chunk_size: int = 600
    chunk_overlap: int = 80


_settings: AssistantSettings | None = None


def get_assistant_settings() -> AssistantSettings:
    """Return the singleton AssistantSettings instance."""
    global _settings
    if _settings is None:
        _settings = AssistantSettings()
    return _settings
