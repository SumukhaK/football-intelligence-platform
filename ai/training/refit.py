"""Serving refit: retrain a chosen run on every completed season (ADR 017).

The source run keeps its season split and stays the model that test results
are quoted from. The refit copies its hyperparameters, imputer and pinned
features, trains on all seasons up to ``last_season`` with the source run's
best tree count, and uses no early stopping because nothing is held out.

The run is written to ``runs/<version>`` only. ``latest/`` and the registry,
which the backend serves from, are left untouched: switching the served model
is a separate, explicit step.

Usage:
    uv run python -m training.refit --source-run models/runs/20260928_123224
        [--last-season 2025/26]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from training.configuration import TrainingConfig
from training.persistence import (
    load_json,
    load_model,
    save_config,
    save_json,
    save_model,
)
from training.pipeline import make_version
from training.splitter import get_feature_columns
from training.trainer import ModelTrainer

PURPOSE = "serving refit"


def refit_config(source_run: Path) -> TrainingConfig:
    """Return the source run's config with its best tree count fixed.

    XGBoost's ``best_iteration`` is zero-based, so the source model predicts
    with ``best_iteration + 1`` trees; the refit grows exactly that many.
    """
    config = TrainingConfig(**load_json(source_run / "config.json"))
    trees = load_model(source_run / "model.joblib").best_iteration + 1
    return config.model_copy(update={"n_estimators": trees})


def refit_rows(
    df: pd.DataFrame, config: TrainingConfig, last_season: str
) -> pd.DataFrame:
    """Return every row up to and including ``last_season``, in date order.

    Raises:
        ValueError: If ``last_season`` is not in the matrix.
    """
    season = df[config.season_column]
    if last_season not in set(season):
        raise ValueError(f"Season {last_season} is not in the feature matrix")
    # Season labels are "YYYY/YY", so string order is chronological order.
    rows = df[season <= last_season]
    return rows.sort_values(config.date_column, kind="stable")


def run_refit(source_run: Path, last_season: str, cwd: Path) -> dict[str, Any]:
    """Train the refit, write ``runs/<version>`` and return its summary."""
    config = refit_config(source_run)
    df = pd.read_parquet(cwd / config.feature_matrix_path)
    rows = refit_rows(df, config, last_season)
    features = get_feature_columns(rows, config)
    model = ModelTrainer().refit(rows[features], rows[config.target_column], config)

    version = make_version()
    run_dir = cwd / config.models_dir / "runs" / version
    run_dir.mkdir(parents=True, exist_ok=True)
    save_model(model, run_dir / "model.joblib")
    save_config(config, run_dir / "config.json")
    seasons = sorted(set(rows[config.season_column]))
    dates = rows[config.date_column].astype(str)
    summary: dict[str, Any] = {
        "version": version,
        "purpose": PURPOSE,
        "source_run": source_run.name,
        "n_estimators": config.n_estimators,
        "first_season": seasons[0],
        "last_season": seasons[-1],
        "excluded_seasons": sorted(set(df[config.season_column]) - set(seasons)),
        "n_train": len(rows),
        "date_range_train": [dates.iloc[0], dates.iloc[-1]],
        "n_features": len(features),
        "run_dir": str(run_dir),
    }
    save_json(summary, run_dir / "refit.json")
    return summary


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success, 1 on failure."""
    parser = argparse.ArgumentParser(prog="training.refit", description=__doc__)
    parser.add_argument("--source-run", required=True, help="Run dir to copy")
    parser.add_argument("--last-season", default="2025/26")
    args = parser.parse_args(argv)
    try:
        summary = run_refit(Path(args.source_run), args.last_season, Path.cwd())
    except Exception as exc:  # noqa: BLE001 — surface any failure as exit code 1
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key, value in summary.items():
        print(f"{key + ':':<18}{value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
