"""CLI: score the served model on a season in progress.

Usage:
    uv run python -m evaluation.in_season_cli --season 2627 --confirm
        [--divisions E0 D1 SP1 I1 F1] [--history PATH] [--model PATH]
        [--base-dir DIR] [--output-dir DIR]

Without ``--confirm`` only the plan is printed. With it, the season's played
matches are downloaded (one raw snapshot per division per day), predicted
from history-only features and scored. Writes ``report.json``, ``report.md``
and ``predictions.csv`` to the output directory.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from config.leagues import TOP_FIVE_DIVISIONS
from config.paths import DataPaths
from evaluation.compare_models import predict_probabilities
from evaluation.in_season import (
    build_season_features,
    evaluate_season,
    fetch_in_progress,
    match_predictions,
)
from ingestion.downloader import HttpxTransport
from ingestion.storage import DatasetStorage
from providers.football_data import FootballDataProvider
from schemas.match import season_label
from training.persistence import load_model, save_json

_FORECASTS = ["candidate", "bookmaker", "priors"]
_NAMES = {"candidate": "Our model", "bookmaker": "Bookmaker", "priors": "Priors"}


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evaluation.in_season_cli")
    parser.add_argument("--season", default="2627", help="Season code, e.g. 2627")
    parser.add_argument("--divisions", nargs="+", default=list(TOP_FIVE_DIVISIONS))
    parser.add_argument("--history", default=None, help="Completed-season CSV")
    parser.add_argument("--model", default="models/latest/model.joblib")
    parser.add_argument("--base-dir", default="../datasets")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--confirm", action="store_true", help="Download files (default: dry run)"
    )
    return parser


def _latest_history(base_dir: Path) -> Path:
    """Return the newest combined completed-season dataset."""
    candidates = sorted(
        (base_dir / "processed" / "football_data").glob("match_results_top5_v*.csv")
    )
    if not candidates:
        raise FileNotFoundError("No match_results_top5 dataset; run the backfill")
    return candidates[-1]


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Download, predict and score; return the report and write outputs."""
    base_dir = Path(args.base_dir)
    today = date.today()
    out = Path(args.output_dir or f"models/backtests/{args.season}_{today:%Y%m%d}")
    history = pd.read_csv(args.history or _latest_history(base_dir))
    current = fetch_in_progress(
        FootballDataProvider(),
        DatasetStorage(DataPaths(base_dir=base_dir)),
        HttpxTransport(),
        args.divisions,
        args.season,
        today,
    )
    rows = build_season_features(history, current, out)
    model = load_model(Path(args.model))
    probs = predict_probabilities(model, rows)
    report = {
        "season": season_label(args.season),
        "as_of": today.isoformat(),
        "model": args.model,
        "last_match": str(rows["match_date"].max()),
        "scores": evaluate_season(rows, probs, history, model.classes),
    }
    save_json(report, out / "report.json")
    (out / "report.md").write_text(render(report), encoding="utf-8")
    match_predictions(rows, probs, model.classes).to_csv(
        out / "predictions.csv", index=False
    )
    return report


def render(report: dict[str, Any]) -> str:
    """Render the in-season report as a Markdown table per league."""
    lines = [
        f"# {report['season']} so far: model vs results",
        "",
        f"Played matches up to {report['last_match']}, scored {report['as_of']}.",
        "Accuracy is the share of matches where the most likely outcome happened.",
        "Log loss rewards confident correct forecasts; lower is better.",
        "",
        "| League | Matches | Our accuracy | Bookmaker accuracy | Our log loss "
        "| Bookmaker log loss | Priors log loss |",
        "|---|---|---|---|---|---|---|",
    ]
    for league, scores in report["scores"].items():
        c, b, p = (scores[k] for k in _FORECASTS)
        lines.append(
            f"| {league} | {int(c['n'])} | {c['accuracy']:.1%} | {b['accuracy']:.1%} "
            f"| {c['log_loss']:.3f} | {b['log_loss']:.3f} | {p['log_loss']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success or dry run, 1 on failure."""
    args = _build_arg_parser().parse_args(argv)
    if not args.confirm:
        print(f"Would download {season_label(args.season)} for {args.divisions}.")
        print("Dry run. Re-run with --confirm to download and score.")
        return 0
    try:
        report = run(args)
    except Exception as exc:  # noqa: BLE001 — surface any failure as exit code 1
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
