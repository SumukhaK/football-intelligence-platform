"""Centralised filesystem path definitions for the data pipeline.

All paths are derived from a single base directory so the project can be
relocated or run in a temporary directory during tests without touching any
other configuration.
"""

from pathlib import Path

from pydantic import BaseModel


class DataPaths(BaseModel):
    """Filesystem layout for the football AI data pipeline.

    Construct via ``DataPaths(base_dir=Path("datasets"))`` or from
    ``Settings.paths``. Call ``ensure_all()`` before writing any files.
    """

    base_dir: Path

    model_config = {"arbitrary_types_allowed": True}

    @property
    def raw(self) -> Path:
        """Immutable raw data as downloaded from providers."""
        return self.base_dir / "raw"

    @property
    def processed(self) -> Path:
        """Cleaned and validated data ready for feature engineering."""
        return self.base_dir / "processed"

    @property
    def cache(self) -> Path:
        """Provider-level cache to avoid redundant downloads."""
        return self.base_dir / "cache"

    @property
    def temp(self) -> Path:
        """Scratch space for in-progress downloads; purged on pipeline restart."""
        return self.base_dir / "temp"

    @property
    def models(self) -> Path:
        """Serialised model artefacts (gitignored)."""
        return self.base_dir / "models"

    def provider_raw_dir(self, provider_id: str) -> Path:
        """Raw directory scoped to a single provider."""
        return self.raw / provider_id

    def provider_cache_dir(self, provider_id: str) -> Path:
        """Cache directory scoped to a single provider."""
        return self.cache / provider_id

    def ensure_all(self) -> None:
        """Create all directories that do not already exist."""
        for directory in (
            self.raw,
            self.processed,
            self.cache,
            self.temp,
            self.models,
        ):
            directory.mkdir(parents=True, exist_ok=True)
