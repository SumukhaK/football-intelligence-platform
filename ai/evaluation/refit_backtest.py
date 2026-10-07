"""Backtest a serving refit against the frozen-split model on a season so far.

Both models score the same played matches of the season, whose features were
built only from earlier matches (``evaluation.in_season_cli`` saves them).
Bookmaker odds are a benchmark only. Paired bootstraps give refit minus
frozen, and each model minus the bookmaker, on the same resampled matches.

Usage:
    uv run python -m evaluation.refit_backtest
        --rows models/backtests/<in-season run>/features/feature_matrix.parquet
        --frozen-run models/runs/20260928_123224 --refit-run models/runs/<v>
        [--season 2026/27] [--through 2026-09-20] [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from evaluation.compare_models import predict_probabilities, score_block
from evaluation.comparison import implied_probabilities, paired_bootstrap_delta
from evaluation.in_season import match_predictions
from training.persistence import load_json, load_model, save_json

_DELTA_METRICS = ["log_loss", "rps", "accuracy"]


def season_rows(matrix: pd.DataFrame, season: str, through: str) -> pd.DataFrame:
    """Return the season's matches played up to ``through``, in date order."""
    dates = pd.to_datetime(matrix["match_date"])
    keep = (matrix["season"] == season) & (dates <= pd.Timestamp(through))
    rows = matrix[keep].sort_values(["match_date", "competition", "home_team"])
    return rows.reset_index(drop=True)


def check_no_leakage(refit: dict[str, Any], rows: pd.DataFrame) -> dict[str, Any]:
    """Confirm the refit saw no backtest season and no match on or after it.

    Raises:
        ValueError: If the refit's training data reaches the backtest matches.
    """
    first = pd.Timestamp(rows["match_date"].min())
    last_trained = pd.Timestamp(refit["date_range_train"][1])
    seasons = set(rows["season"])
    # Season labels are "YYYY/YY", so string order is chronological order.
    if last_trained >= first or min(seasons) <= refit["last_season"]:
        raise ValueError(
            f"Refit trained up to {last_trained.date()} ({refit['last_season']}),"
            f" which overlaps backtest matches from {first.date()}"
        )
    return {
        "refit_last_training_match": str(last_trained.date()),
        "first_backtest_match": str(first.date()),
        "refit_last_season": refit["last_season"],
        "backtest_seasons": sorted(seasons),
    }


def compare(
    rows: pd.DataFrame, frozen: np.ndarray, refit: np.ndarray, classes: list[str]
) -> dict[str, Any]:
    """Score both models and the bookmaker, with paired bootstrap deltas."""
    y = rows["result"].to_numpy()
    book = implied_probabilities(rows, classes)
    deltas: dict[str, Any] = {
        f"refit_minus_frozen_{m}": paired_bootstrap_delta(
            y, refit, frozen, classes, metric=m
        ).__dict__
        for m in _DELTA_METRICS
    }
    for name, probs in [("refit", refit), ("frozen", frozen)]:
        for m in _DELTA_METRICS:
            deltas[f"{name}_minus_bookmaker_{m}"] = paired_bootstrap_delta(
                y, probs, book, classes, metric=m
            ).__dict__
    scores = score_block(rows, {"frozen": frozen, "refit": refit}, classes)
    return {"scores": scores, "deltas": deltas}


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Load both models and the season rows, score, and write the outputs."""
    frozen_run, refit_run = Path(args.frozen_run), Path(args.refit_run)
    frozen_model = load_model(frozen_run / "model.joblib")
    refit_model = load_model(refit_run / "model.joblib")
    if frozen_model.classes != refit_model.classes:
        raise ValueError("Models disagree on class order")
    refit_info = load_json(refit_run / "refit.json")
    rows = season_rows(pd.read_parquet(args.rows), args.season, args.through)
    classes = refit_model.classes
    frozen = predict_probabilities(frozen_model, rows)
    refit = predict_probabilities(refit_model, rows)
    report = {
        "season": args.season,
        "through": args.through,
        "frozen_model": frozen_run.name,
        "refit_model": refit_run.name,
        "matches": len(rows),
        "leakage_check": check_no_leakage(refit_info, rows),
        **compare(rows, frozen, refit, classes),
    }
    out = Path(args.output_dir or f"models/backtests/refit_{refit_run.name}")
    save_json(report, out / "report.json")
    for name, probs in [("frozen", frozen), ("refit", refit)]:
        match_predictions(rows, probs, classes).to_csv(
            out / f"predictions_{name}.csv", index=False
        )
    (out / "report.md").write_text(render(report), encoding="utf-8")
    return report


def render(report: dict[str, Any]) -> str:
    """Render the per-league table and the bootstrap deltas as Markdown."""
    lines = [
        f"# {report['season']} up to {report['through']}: refit vs frozen",
        "",
        f"Frozen `{report['frozen_model']}`, refit `{report['refit_model']}`,"
        f" {report['matches']} matches.",
        "",
        "| League | Matches | Model | Accuracy | Log loss | RPS | Brier |",
        "|---|---|---|---|---|---|---|",
    ]
    for league, scores in report["scores"].items():
        for name in ["frozen", "refit", "bookmaker"]:
            s = scores[name]
            lines.append(
                f"| {league} | {int(s['n'])} | {name} | {s['accuracy']:.1%} "
                f"| {s['log_loss']:.3f} | {s['rps']:.4f} | {s['brier']:.4f} |"
            )
    lines += ["", "| Paired bootstrap | Mean | 95% interval |", "|---|---|---|"]
    for name, d in report["deltas"].items():
        lines.append(
            f"| {name} | {d['mean']:+.4f} | {d['lower']:+.4f} to {d['upper']:+.4f} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success, 1 on failure."""
    parser = argparse.ArgumentParser(prog="evaluation.refit_backtest")
    parser.add_argument("--rows", required=True, help="Saved in-season features")
    parser.add_argument("--frozen-run", required=True)
    parser.add_argument("--refit-run", required=True)
    parser.add_argument("--season", default="2026/27")
    parser.add_argument("--through", default="2026-09-20")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    try:
        report = run(args)
    except Exception as exc:  # noqa: BLE001 — surface any failure as exit code 1
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
