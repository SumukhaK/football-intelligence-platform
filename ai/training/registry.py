"""Adapter that builds a ModelEntry and appends it to the local registry."""

from __future__ import annotations

import importlib.metadata
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from model_registry.registry import ModelEntry, ModelRegistry
from training.configuration import TrainingConfig


def _git_commit() -> str | None:
    """Return the current HEAD commit hash, or None if git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() or None if result.returncode == 0 else None
    except Exception:  # noqa: BLE001
        return None


def _framework_versions() -> dict[str, str]:
    """Return installed versions of key ML packages."""
    pkgs = ["xgboost", "scikit-learn", "pandas", "numpy", "joblib", "pyarrow"]
    versions: dict[str, str] = {}
    for pkg in pkgs:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg] = "unknown"
    return versions


def register_model(
    *,
    version: str,
    run_dir: Path,
    config: TrainingConfig,
    test_metrics: dict[str, float],
    registry_path: Path,
    source_dataset_version: str,
) -> ModelEntry:
    """Build a ModelEntry from training artifacts and write it to the registry."""
    entry = ModelEntry(
        version=version,
        created_at=datetime.now(tz=UTC),
        run_dir=str(run_dir),
        source_dataset_version=source_dataset_version,
        feature_matrix_path=config.feature_matrix_path,
        git_commit=_git_commit(),
        framework_versions=_framework_versions(),
        metrics=test_metrics,
    )
    ModelRegistry(registry_path).register(entry)
    return entry
