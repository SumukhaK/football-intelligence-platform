"""Training pipeline: load feature matrix → train → evaluate → persist → register."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from evaluation.cross_validation import (
    CVSummary,
    run_cross_validation,
    run_season_cross_validation,
)
from evaluation.metrics import compute_confusion_matrix, compute_metrics
from evaluation.plots import save_confusion_matrix, save_feature_importance
from evaluation.reports import CVReport, EvaluationReport, FoldResult, SplitMetrics
from training.configuration import TrainingConfig
from training.model_card import describe_dataset, write_model_card
from training.persistence import load_json, save_config, save_json, save_model
from training.registry import register_model
from training.splitter import DataSplit, get_feature_columns, make_splitter
from training.trainer import ModelTrainer, TrainedModel

_DEFAULT_FEATURE_MATRIX = "datasets/features/feature_matrix.parquet"
_DEFAULT_MODELS_DIR = "models"


def _make_version() -> str:
    """Generate a sortable UTC timestamp version string."""
    return datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")


def _extract_dataset_version(feature_matrix_path: Path) -> str:
    """Read source_dataset_version from the sibling feature_metadata.json."""
    metadata_path = feature_matrix_path.parent / "feature_metadata.json"
    if metadata_path.exists():
        meta = load_json(metadata_path)
        return str(meta.get("source_dataset_version", "unknown"))
    return "unknown"


def _build_split_metrics(
    y_true: pd.Series,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    classes: list[str],
) -> SplitMetrics:
    """Compute all metrics for one split and wrap in a SplitMetrics."""
    m = compute_metrics(y_true, y_pred, y_prob, classes)
    cm = compute_confusion_matrix(y_true, y_pred, classes)
    return SplitMetrics(
        accuracy=m["accuracy"],
        precision_weighted=m["precision_weighted"],
        recall_weighted=m["recall_weighted"],
        f1_weighted=m["f1_weighted"],
        log_loss=m["log_loss"],
        roc_auc_ovr=m["roc_auc_ovr"],
        confusion_matrix=cm,
    )


def _build_cv_report(summary: CVSummary) -> CVReport:
    """Convert a CVSummary dataclass into the Pydantic CVReport model."""
    return CVReport(
        n_folds=summary.n_folds,
        fold_results=[
            FoldResult(
                fold=r.fold,
                train_size=r.train_size,
                val_size=r.val_size,
                accuracy=r.accuracy,
                f1_weighted=r.f1_weighted,
                log_loss=r.log_loss,
            )
            for r in summary.fold_results
        ],
        mean_accuracy=summary.mean_accuracy,
        std_accuracy=summary.std_accuracy,
        mean_f1=summary.mean_f1,
        std_f1=summary.std_f1,
        mean_log_loss=summary.mean_log_loss,
        std_log_loss=summary.std_log_loss,
    )


def _persist_run(
    *,
    model: TrainedModel,
    report: EvaluationReport,
    config: TrainingConfig,
    run_dir: Path,
    split: DataSplit,
    y_test_pred: np.ndarray,
) -> None:
    """Write all artifacts for a single run directory."""
    run_dir.mkdir(parents=True, exist_ok=True)
    save_model(model, run_dir / "model.joblib")
    save_config(config, run_dir / "config.json")
    test_m = report.test_metrics
    save_json(
        {
            "train": {
                "accuracy": report.train_metrics.accuracy,
                "log_loss": report.train_metrics.log_loss,
            },
            "val": {
                "accuracy": report.val_metrics.accuracy,
                "log_loss": report.val_metrics.log_loss,
            },
            "test": {
                "accuracy": test_m.accuracy,
                "precision_weighted": test_m.precision_weighted,
                "recall_weighted": test_m.recall_weighted,
                "f1_weighted": test_m.f1_weighted,
                "log_loss": test_m.log_loss,
                "roc_auc_ovr": test_m.roc_auc_ovr,
            },
        },
        run_dir / "metrics.json",
    )
    save_json(json.loads(report.model_dump_json()), run_dir / "evaluation_report.json")

    plots_dir = run_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    save_confusion_matrix(
        split.y_test, y_test_pred, model.classes, plots_dir / "confusion_matrix.png"
    )
    save_feature_importance(
        model.booster, model.feature_names, plots_dir / "feature_importance.png"
    )


def _promote_run(
    *,
    run_dir: Path,
    models_dir: Path,
    report: EvaluationReport,
    config: TrainingConfig,
    version: str,
    source_version: str,
) -> None:
    """Copy a run to latest/, write the global report and register it."""
    latest_dir = models_dir / "latest"
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    shutil.copytree(run_dir, latest_dir)

    eval_dir = models_dir / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    save_json(json.loads(report.model_dump_json()), eval_dir / "evaluation_report.json")

    register_model(
        version=version,
        run_dir=run_dir,
        config=config,
        test_metrics={
            k: v
            for k, v in json.loads(report.test_metrics.model_dump_json()).items()
            if isinstance(v, float)
        },
        registry_path=models_dir / "registry.json",
        source_dataset_version=source_version,
    )


class TrainingPipeline:
    """Orchestrates the end-to-end training, evaluation, and registration flow."""

    def __init__(self, config: TrainingConfig | None = None) -> None:
        """Initialise with an optional config; defaults to TrainingConfig()."""
        self._config = config or TrainingConfig()

    def run(self, cwd: Path, promote: bool = True) -> dict[str, Any]:
        """Execute the full pipeline and return a summary of key results.

        With ``promote=False`` the run is written only to ``runs/<version>``:
        ``latest/``, the global evaluation report and the registry, which the
        backend serves from, are left untouched.
        """
        config = self._config
        version = _make_version()

        feature_matrix_path = cwd / config.feature_matrix_path
        models_dir = cwd / config.models_dir
        run_dir = models_dir / "runs" / version

        # Step 1 — Load
        df = pd.read_parquet(feature_matrix_path)
        feature_cols = get_feature_columns(df, config)

        # Step 2 — Split
        split = make_splitter(config).split(df, feature_cols, config)

        # Step 3 — Train
        trainer = ModelTrainer()
        model = trainer.train(split, config)

        # Step 4 — Cross-validation (on train+val, time-ordered)
        X_cv = pd.concat([split.X_train, split.X_val])
        y_cv = pd.concat([split.y_train, split.y_val])
        if config.split_strategy == "season":
            seasons = df.loc[X_cv.index, config.season_column]
            cv_summary = run_season_cross_validation(X_cv, y_cv, seasons, config)
        else:
            cv_summary = run_cross_validation(X_cv, y_cv, config)

        # Step 5 — Evaluate all splits
        y_train_pred, y_train_prob = trainer.predict(model, split.X_train)
        y_val_pred, y_val_prob = trainer.predict(model, split.X_val)
        y_test_pred, y_test_prob = trainer.predict(model, split.X_test)

        train_metrics = _build_split_metrics(
            split.y_train, y_train_pred, y_train_prob, model.classes
        )
        val_metrics = _build_split_metrics(
            split.y_val, y_val_pred, y_val_prob, model.classes
        )
        test_metrics = _build_split_metrics(
            split.y_test, y_test_pred, y_test_prob, model.classes
        )

        # Step 6 — Build report
        cv_report = _build_cv_report(cv_summary)
        report = EvaluationReport(
            model_version=version,
            evaluation_timestamp=datetime.now(tz=UTC),
            train_metrics=train_metrics,
            val_metrics=val_metrics,
            test_metrics=test_metrics,
            cv_report=cv_report,
            classes=model.classes,
            n_features=len(feature_cols),
            n_train=split.train_size,
            n_val=split.val_size,
            n_test=split.test_size,
        )

        # Step 7 — Persist run artifacts
        _persist_run(
            model=model,
            report=report,
            config=config,
            run_dir=run_dir,
            split=split,
            y_test_pred=y_test_pred,
        )

        # Step 8 — Model card in the run directory
        write_model_card(
            model=model,
            report=report,
            version=version,
            dataset=describe_dataset(df, config),
            config=config,
            output_path=run_dir / "model_card.md",
        )

        # Step 9 — Promote: latest/, global report and registry
        if promote:
            _promote_run(
                run_dir=run_dir,
                models_dir=models_dir,
                report=report,
                config=config,
                version=version,
                source_version=_extract_dataset_version(feature_matrix_path),
            )

        return {
            "version": version,
            "test_accuracy": test_metrics.accuracy,
            "test_f1": test_metrics.f1_weighted,
            "test_log_loss": test_metrics.log_loss,
            "best_iteration": model.best_iteration,
            "n_features": len(feature_cols),
            "run_dir": str(run_dir),
            "promoted": promote,
        }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the training pipeline."""
    parser = argparse.ArgumentParser(
        description="Train the XGBoost match outcome model.",
        prog="training.pipeline",
    )
    parser.add_argument(
        "--feature-matrix",
        metavar="PATH",
        help=(
            "Path to feature_matrix.parquet. "
            "Defaults to datasets/features/feature_matrix.parquet."
        ),
    )
    parser.add_argument(
        "--models-dir",
        metavar="DIR",
        default=_DEFAULT_MODELS_DIR,
        help=(
            "Output directory for model artifacts. "
            f"Defaults to '{_DEFAULT_MODELS_DIR}'."
        ),
    )
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--split-strategy", choices=["chronological", "season"], default=None
    )
    parser.add_argument("--val-seasons", nargs="+", metavar="SEASON")
    parser.add_argument("--test-seasons", nargs="+", metavar="SEASON")
    parser.add_argument("--holdout-seasons", nargs="+", metavar="SEASON")
    parser.add_argument(
        "--no-promote",
        action="store_true",
        help="Write the run only; leave latest/ and the registry untouched.",
    )
    args = parser.parse_args(argv)

    overrides: dict[str, Any] = {
        "n_estimators": args.n_estimators,
        "learning_rate": args.learning_rate,
        "max_depth": args.max_depth,
        "random_seed": args.seed,
        "models_dir": args.models_dir,
    }
    if args.feature_matrix:
        overrides["feature_matrix_path"] = args.feature_matrix
    optional = {
        "split_strategy": args.split_strategy,
        "val_seasons": args.val_seasons,
        "test_seasons": args.test_seasons,
        "holdout_seasons": args.holdout_seasons,
    }
    overrides.update({k: v for k, v in optional.items() if v is not None})

    config = TrainingConfig(**overrides)
    cwd = Path.cwd()

    print(f"Feature matrix: {cwd / config.feature_matrix_path}")
    print(f"Models dir:     {cwd / config.models_dir}")
    print(
        f"Estimators:     {config.n_estimators}"
        f"  |  LR: {config.learning_rate}"
        f"  |  Depth: {config.max_depth}"
    )
    print()

    try:
        pipeline = TrainingPipeline(config)
        result = pipeline.run(cwd, promote=not args.no_promote)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Version:        {result['version']}")
    print(f"Best iteration: {result['best_iteration']}")
    print(f"Features used:  {result['n_features']}")
    print(f"Test accuracy:  {result['test_accuracy']:.4f}")
    print(f"Test F1:        {result['test_f1']:.4f}")
    print(f"Test log-loss:  {result['test_log_loss']:.4f}")
    print(f"Run dir:        {result['run_dir']}")
    print(f"Promoted:       {'yes' if result['promoted'] else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
