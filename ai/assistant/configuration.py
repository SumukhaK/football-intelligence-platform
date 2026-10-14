"""Assistant configuration loaded from environment variables or .env file."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AssistantSettings(BaseSettings):
    """Runtime configuration for the Football Intelligence Assistant."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # ai/.env is shared by all three settings classes, so each ignores the
        # keys that belong to the others.
        extra="ignore",
    )

    # Who embeds and answers (ADR 025); the backend handles "off" itself.
    assistant_provider: Literal["ollama", "workers_ai"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen2.5:7b-instruct"
    ollama_embed_model: str = "nomic-embed-text"

    workers_ai_account_id: str | None = None
    workers_ai_api_token: SecretStr | None = None
    workers_ai_chat_model: str = "@cf/google/gemma-4-26b-a4b-it"
    workers_ai_embed_model: str = "@cf/qwen/qwen3-embedding-0.6b"
    workers_ai_timeout_s: float = Field(default=20.0, gt=0)
    # Reasoning models think before answering unless told not to; off keeps
    # answers inside the app's 30-second request budget.
    workers_ai_thinking: bool = False
    # The Llama Guard model that checks each question (ADR 027).
    ollama_guard_model: str = "llama-guard3:1b"
    workers_ai_guard_model: str = "@cf/meta/llama-guard-3-8b"

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
