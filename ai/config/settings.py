"""Application settings loaded from environment variables.

All settings are prefixed with ``FOOTBALL_AI_`` in the environment.
An ``.env`` file at the project root is loaded automatically when present.

Example .env:
    FOOTBALL_AI_DATASETS_BASE_DIR=./datasets
    FOOTBALL_AI_LOG_LEVEL=DEBUG
    FOOTBALL_AI_HTTP_TIMEOUT_SECONDS=60
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.paths import DataPaths
from shared.constants import DEFAULT_HTTP_MAX_RETRIES, DEFAULT_HTTP_TIMEOUT


class Settings(BaseSettings):
    """Runtime configuration for the football AI workspace."""

    model_config = SettingsConfigDict(
        env_prefix="FOOTBALL_AI_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    datasets_base_dir: Path = Field(
        default=Path("datasets"),
        description="Root directory for all raw, processed, and cached datasets.",
    )
    log_level: str = Field(
        default="INFO",
        description="Python logging level: DEBUG, INFO, WARNING, ERROR.",
    )
    http_timeout_seconds: int = Field(
        default=DEFAULT_HTTP_TIMEOUT,
        description="Timeout in seconds for provider HTTP requests.",
        gt=0,
    )
    http_max_retries: int = Field(
        default=DEFAULT_HTTP_MAX_RETRIES,
        description="Maximum number of retry attempts for failed HTTP requests.",
        ge=0,
    )

    @property
    def paths(self) -> DataPaths:
        """Return the data path layout derived from ``datasets_base_dir``."""
        return DataPaths(base_dir=self.datasets_base_dir)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
