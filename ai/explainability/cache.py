"""In-process explainer cache — avoids rebuilding TreeExplainer unnecessarily.

The cache is a class-level dict keyed by model version string.
It is process-local, thread-safe for reads, and is cleared via ExplainerCache.clear().

Caching behaviour:
  - First call for a version loads the model from disk and builds the TreeExplainer.
  - Subsequent calls for the same version return the cached instance immediately.
  - Different versions are cached independently.
  - clear() resets all entries (useful in tests and when memory is a concern).
"""

from __future__ import annotations

from pathlib import Path

from explainability.explainer import SHAPExplainer
from training.persistence import load_model


class ExplainerCache:
    """Class-level cache mapping model version → SHAPExplainer."""

    _cache: dict[str, SHAPExplainer] = {}

    @classmethod
    def get_or_create(cls, model_path: Path, version: str) -> SHAPExplainer:
        """Return a cached SHAPExplainer for version, loading it if absent."""
        if version not in cls._cache:
            model = load_model(model_path)
            cls._cache[version] = SHAPExplainer(model)
        return cls._cache[version]

    @classmethod
    def clear(cls) -> None:
        """Remove all cached explainers."""
        cls._cache.clear()

    @classmethod
    def size(cls) -> int:
        """Return the number of cached entries."""
        return len(cls._cache)
