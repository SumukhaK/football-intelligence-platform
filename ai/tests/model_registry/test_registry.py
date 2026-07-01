"""Tests for model_registry.registry."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from model_registry.registry import ModelEntry, ModelRegistry


def _make_entry(version: str = "20240101_120000") -> ModelEntry:
    """Return a valid ModelEntry for testing."""
    return ModelEntry(
        version=version,
        created_at=datetime.now(tz=UTC),
        run_dir=f"models/runs/{version}",
        source_dataset_version="unknown",
        feature_matrix_path="datasets/features/feature_matrix.parquet",
        git_commit=None,
        framework_versions={"xgboost": "2.0.0", "python": "3.12.0"},
        metrics={"accuracy": 0.5, "f1_weighted": 0.45},
    )


def test_registry_starts_empty(tmp_path: Path) -> None:
    """A fresh registry has no versions."""
    registry = ModelRegistry(tmp_path / "registry.json")
    assert registry.list_versions() == []
    assert registry.latest() is None


def test_register_adds_entry(tmp_path: Path) -> None:
    """Registering an entry makes it appear in list_versions."""
    registry = ModelRegistry(tmp_path / "registry.json")
    entry = _make_entry("v1")
    registry.register(entry)
    versions = registry.list_versions()
    assert len(versions) == 1
    assert versions[0].version == "v1"


def test_latest_returns_last_registered(tmp_path: Path) -> None:
    """latest() must return the most recently registered entry."""
    registry = ModelRegistry(tmp_path / "registry.json")
    registry.register(_make_entry("v1"))
    registry.register(_make_entry("v2"))
    latest = registry.latest()
    assert latest is not None
    assert latest.version == "v2"


def test_registry_persists_across_instances(tmp_path: Path) -> None:
    """A second ModelRegistry instance reading the same file sees prior entries."""
    path = tmp_path / "registry.json"
    ModelRegistry(path).register(_make_entry("v1"))
    loaded = ModelRegistry(path).list_versions()
    assert len(loaded) == 1
    assert loaded[0].version == "v1"


def test_entry_is_frozen() -> None:
    """ModelEntry must be immutable."""
    entry = _make_entry()
    with pytest.raises(Exception):  # noqa: B017
        entry.version = "changed"


def test_register_multiple_entries(tmp_path: Path) -> None:
    """Registering three entries stores all three."""
    registry = ModelRegistry(tmp_path / "registry.json")
    for v in ["v1", "v2", "v3"]:
        registry.register(_make_entry(v))
    assert len(registry.list_versions()) == 3
