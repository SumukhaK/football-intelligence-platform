"""Hyperparameter search by season walk-forward CV on training seasons only.

Validation, test and holdout seasons are never seen during the search, so the
test comparison in ADR 007 stays an honest estimate.

Usage:
    uv run python -m training.tuning --feature-matrix PATH
        --val-seasons 2022/23 --test-seasons 2023/24
        [--holdout-seasons 2024/25 2025/26] [--max-depths 2 3 4]
        [--learning-rates 0.03 0.05 0.1] [--n-estimators 100 200 400]
        [--cv-folds 5] [--output PATH]
"""

from __future__ import annotations

import argparse
import itertools
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from evaluation.cross_validation import run_season_cross_validation
from training.configuration import TrainingConfig
from training.persistence import save_json
from training.splitter import SeasonSplitter, get_feature_columns


@dataclass(frozen=True)
class TuningResult:
    """Season-CV scores for one hyperparameter setting."""

    params: dict[str, Any]
    mean_log_loss: float
    std_log_loss: float
    mean_accuracy: float
    fold_train_sizes: list[int]
    fold_val_sizes: list[int]


def parameter_grid(
    max_depths: list[int], learning_rates: list[float], n_estimators: list[int]
) -> list[dict[str, Any]]:
    """Return every combination of the given hyperparameter values."""
    return [
        {"max_depth": d, "learning_rate": lr, "n_estimators": n}
        for d, lr, n in itertools.product(max_depths, learning_rates, n_estimators)
    ]


def tune(
    df: pd.DataFrame,
    feature_cols: list[str],
    config: TrainingConfig,
    grid: list[dict[str, Any]],
) -> list[TuningResult]:
    """Score each setting by season CV on training seasons, best first.

    Raises:
        ValueError: If ``grid`` is empty.
    """
    if not grid:
        raise ValueError("Parameter grid is empty")
    split = SeasonSplitter().split(df, feature_cols, config)
    seasons = df.loc[split.X_train.index, config.season_column]
    results = []
    for params in grid:
        summary = run_season_cross_validation(
            split.X_train, split.y_train, seasons, config.model_copy(update=params)
        )
        results.append(
            TuningResult(
                params=params,
                mean_log_loss=summary.mean_log_loss,
                std_log_loss=summary.std_log_loss,
                mean_accuracy=summary.mean_accuracy,
                fold_train_sizes=[r.train_size for r in summary.fold_results],
                fold_val_sizes=[r.val_size for r in summary.fold_results],
            )
        )
    return sorted(results, key=lambda r: r.mean_log_loss)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="training.tuning")
    parser.add_argument("--feature-matrix", required=True)
    parser.add_argument("--val-seasons", nargs="+", required=True)
    parser.add_argument("--test-seasons", nargs="+", required=True)
    parser.add_argument("--holdout-seasons", nargs="+", default=[])
    parser.add_argument("--max-depths", nargs="+", type=int, default=[2, 3, 4])
    parser.add_argument(
        "--learning-rates", nargs="+", type=float, default=[0.03, 0.05, 0.1]
    )
    parser.add_argument("--n-estimators", nargs="+", type=int, default=[100, 200, 400])
    parser.add_argument("--cv-folds", type=int, default=5)
    parser.add_argument("--output", default="models/tuning/tuning_results.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success, 1 on failure."""
    args = _build_arg_parser().parse_args(argv)
    config = TrainingConfig(
        split_strategy="season",
        val_seasons=args.val_seasons,
        test_seasons=args.test_seasons,
        holdout_seasons=args.holdout_seasons,
        cv_folds=args.cv_folds,
    )
    grid = parameter_grid(args.max_depths, args.learning_rates, args.n_estimators)
    try:
        df = pd.read_parquet(args.feature_matrix)
        results = tune(df, get_feature_columns(df, config), config, grid)
    except Exception as exc:  # noqa: BLE001 — surface any failure as exit code 1
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    save_json({"results": [asdict(r) for r in results]}, output)
    print("depth  lr     trees  cv log loss (std)   cv accuracy")
    for r in results:
        p = r.params
        print(
            f"{p['max_depth']:<6} {p['learning_rate']:<6} {p['n_estimators']:<6} "
            f"{r.mean_log_loss:.4f} ({r.std_log_loss:.4f})     {r.mean_accuracy:.3f}"
        )
    print(f"\nResults: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
