"""Serve a backtested refit: copy it to ``latest/`` and register it (ADR 017).

The refit has no held-out test set, so its registry metrics are its scores on
the current-season backtest, under names that say so. The global evaluation
report in ``models/evaluation/`` is left alone: test and holdout results stay
quoted from the frozen-split reporting model.

Usage:
    uv run python -m training.promote_refit --run models/runs/<v>
        --backtest models/backtests/refit_<v>/report.json
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

from training.configuration import TrainingConfig
from training.persistence import load_json, save_json
from training.pipeline import extract_dataset_version
from training.registry import register_model

_SCORES = ["accuracy", "log_loss", "rps", "brier"]


def backtest_metrics(report: dict[str, Any], version: str) -> dict[str, float]:
    """Return the refit's overall backtest scores, named by season.

    Raises:
        ValueError: If the backtest report is for a different refit.
    """
    if report["refit_model"] != version:
        raise ValueError(f"Backtest is for {report['refit_model']}, not {version}")
    suffix = report["season"].replace("/", "_")
    overall = report["scores"]["overall"]["refit"]
    return {f"{name}_{suffix}": float(overall[name]) for name in _SCORES}


def model_card(info: dict[str, Any], metrics: dict[str, float]) -> str:
    """Return a short Markdown model card for a promoted refit."""
    lines = [
        f"# Model card: {info['version']}",
        "",
        f"- Purpose: {info['purpose']} of `{info['source_run']}` (ADR 017)",
        f"- Trained on: {info['first_season']} to {info['last_season']}"
        f" ({info['n_train']} matches, {info['n_features']} features)",
        f"- Trees: {info['n_estimators']}, fixed, no early stopping",
        "- No held-out test set: test and holdout results are quoted from"
        f" `{info['source_run']}`.",
        "",
        "## Current-season backtest",
        "",
    ]
    lines += [f"- {name}: {value:.4f}" for name, value in metrics.items()]
    return "\n".join(lines) + "\n"


def promote(run_dir: Path, backtest: Path, models_dir: Path) -> dict[str, float]:
    """Copy ``run_dir`` to ``latest/`` and append it to the registry."""
    info = load_json(run_dir / "refit.json")
    metrics = backtest_metrics(load_json(backtest), info["version"])
    save_json(metrics, run_dir / "metrics.json")
    (run_dir / "model_card.md").write_text(model_card(info, metrics), "utf-8")

    config = TrainingConfig(**load_json(run_dir / "config.json"))
    latest = models_dir / "latest"
    if latest.exists():
        shutil.rmtree(latest)
    shutil.copytree(run_dir, latest)
    register_model(
        version=info["version"],
        run_dir=run_dir,
        config=config,
        test_metrics=metrics,
        registry_path=models_dir / "registry.json",
        source_dataset_version=extract_dataset_version(
            models_dir.parent / config.feature_matrix_path
        ),
    )
    return metrics


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success, 1 on failure."""
    parser = argparse.ArgumentParser(prog="training.promote_refit")
    parser.add_argument("--run", required=True, help="Refit run directory")
    parser.add_argument("--backtest", required=True, help="refit_backtest report")
    parser.add_argument("--models-dir", default="models")
    args = parser.parse_args(argv)
    try:
        metrics = promote(Path(args.run), Path(args.backtest), Path(args.models_dir))
    except Exception as exc:  # noqa: BLE001 — surface any failure as exit code 1
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Promoted {Path(args.run).name}: {metrics}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
