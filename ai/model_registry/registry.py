"""Local filesystem model registry backed by a JSON index file."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class ModelEntry(BaseModel):
    """A single registered model version."""

    model_config = {"frozen": True}
    version: str
    created_at: datetime
    run_dir: str
    source_dataset_version: str
    feature_matrix_path: str
    git_commit: str | None
    framework_versions: dict[str, str]
    metrics: dict[str, float]


class ModelRegistry:
    """Tracks trained model versions in a local JSON registry file."""

    def __init__(self, registry_path: Path) -> None:
        """Initialise with path to the JSON registry file."""
        self._path = registry_path

    def register(self, entry: ModelEntry) -> None:
        """Append a new model entry to the registry."""
        entries = self._load()
        entries.append(json.loads(entry.model_dump_json()))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    def list_versions(self) -> list[ModelEntry]:
        """Return all registered model versions, oldest first."""
        return [ModelEntry(**e) for e in self._load()]

    def latest(self) -> ModelEntry | None:
        """Return the most recently registered model, or None if empty."""
        entries = self.list_versions()
        return entries[-1] if entries else None

    def _load(self) -> list[dict[str, Any]]:
        """Load the registry JSON, returning an empty list if it does not exist."""
        if not self._path.exists():
            return []
        raw: list[dict[str, Any]] = json.loads(self._path.read_text(encoding="utf-8"))
        return raw
