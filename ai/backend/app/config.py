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


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the singleton Settings instance (cached after first call)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
