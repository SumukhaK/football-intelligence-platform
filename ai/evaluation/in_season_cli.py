"""CLI: score the served model on a season in progress.

Usage:
    uv run python -m evaluation.in_season_cli --season 2627 --confirm
        [--divisions E0 D1 SP1 I1 F1] [--history PATH] [--model PATH]
        [--base-dir DIR] [--output-dir DIR] [--through YYYY-MM-DD]
    uv run python -m evaluation.in_season_cli --season 2627 --confirm
        --features models/backtests/<run>/features/feature_matrix.parquet

Without ``--confirm`` only the plan is printed. With it, the season's played
matches are downloaded (one raw snapshot per division per day), predicted
from history-only features and scored. ``--features`` rescores a saved run's
feature matrix instead of downloading. Writes ``report.json``, ``report.md``
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
    BOOTSTRAP_METRICS,
    build_season_features,
    evaluate_season,
    match_predictions,
    split_season,
)
from ingestion.downloader import HttpxTransport
from ingestion.in_progress import fetch_in_progress
from ingestion.storage import DatasetStorage
from providers.football_data import FootballDataProvider
from schemas.match import season_label
from training.persistence import load_model, save_json

_NAMES = {"candidate": "Our model", "elo": "Elo only", "bookmaker": "Bet365"}


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evaluation.in_season_cli")
    parser.add_argument("--season", default="2627", help="Season code, e.g. 2627")
    parser.add_argument("--divisions", nargs="+", default=list(TOP_FIVE_DIVISIONS))
    parser.add_argument("--history", default=None, help="Completed-season CSV")
    parser.add_argument("--model", default="models/latest/model.joblib")
    parser.add_argument("--base-dir", default="../datasets")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--features", default=None, help="Saved feature matrix; skips the download"
    )
    parser.add_argument("--through", default=None, help="Last match date to score")
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


def _build_matrix(args: argparse.Namespace, out: Path) -> pd.DataFrame:
    """Download the season so far and build features over history plus it."""
    base_dir = Path(args.base_dir)
    current = fetch_in_progress(
        FootballDataProvider(),
        DatasetStorage(DataPaths(base_dir=base_dir)),
        HttpxTransport(),
        args.divisions,
        args.season,
        date.today(),
    )
    history = pd.read_csv(args.history or _latest_history(base_dir))
    return build_season_features(history, current, out)


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Download (or reuse) features, predict and score; write the outputs."""
    today = date.today()
    out = Path(args.output_dir or f"models/backtests/{args.season}_{today:%Y%m%d}")
    matrix = (
        pd.read_parquet(args.features) if args.features else _build_matrix(args, out)
    )
    history, rows = split_season(matrix, season_label(args.season), args.through)
    model = load_model(Path(args.model))
    probs = predict_probabilities(model, rows)
    report = {
        "season": season_label(args.season),
        "as_of": today.isoformat(),
        "model": args.model,
        "last_match": str(rows["match_date"].max()),
        **evaluate_season(rows, probs, history, model.classes),
    }
    save_json(report, out / "report.json")
    (out / "report.md").write_text(render(report), encoding="utf-8")
    match_predictions(rows, probs, model.classes).to_csv(
        out / "predictions.csv", index=False
    )
    return report


def render(report: dict[str, Any]) -> str:
    """Render the in-season report: per-league table, then bootstrap ranges."""
    lines = [
        f"# {report['season']} so far: model vs results",
        "",
        f"Played matches up to {report['last_match']}, scored {report['as_of']}.",
        "Accuracy is the share of matches where the most likely outcome happened.",
        "Log loss rewards confident correct forecasts; lower is better.",
        "Bet365 is its pre-match odds with the margin removed: a benchmark only,",
        "never a model input. Elo only is fitted on the Elo gap in earlier seasons.",
        "",
        "| League | Matches | Our accuracy | Elo accuracy | Bet365 accuracy "
        "| Our log loss | Elo log loss | Bet365 log loss | Priors log loss |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for league, s in report["scores"].items():
        c, e, b = s["candidate"], s["elo"], s["bookmaker"]
        lines.append(
            f"| {league} | {int(c['n'])} | {c['accuracy']:.1%} | {e['accuracy']:.1%} "
            f"| {b['accuracy']:.1%} | {c['log_loss']:.3f} | {e['log_loss']:.3f} "
            f"| {b['log_loss']:.3f} | {s['priors']['log_loss']:.3f} |"
        )
    return "\n".join(lines + _render_bootstrap(report)) + "\n"


def _render_bootstrap(report: dict[str, Any]) -> list[str]:
    """Overall 95% bootstrap ranges and paired model-minus-benchmark deltas."""
    overall = report["scores"]["overall"]
    header = "| | " + " | ".join(BOOTSTRAP_METRICS) + " |"
    rule = "|---" * (len(BOOTSTRAP_METRICS) + 1) + "|"
    lines = ["", "## Overall, with 95% bootstrap ranges", "", header, rule]
    for name, ranges in report["intervals"].items():
        cells = [
            f"{_fmt(m, overall[name][m])} ({_fmt(m, lo)} to {_fmt(m, hi)})"
            for m, (lo, hi) in ranges.items()
        ]
        lines.append(f"| {_NAMES[name]} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "Paired bootstrap of our model minus each benchmark on the same resampled",
        "matches. Negative is better, except accuracy (percentage points), where",
        "positive is better.",
        "",
        header,
        rule,
    ]
    for name, deltas in report["deltas"].items():
        other = _NAMES[name.removeprefix("candidate_minus_")]
        cells = [
            f"{_delta(m, d['mean'])} "
            f"({_delta(m, d['lower'])} to {_delta(m, d['upper'])})"
            for m, d in deltas.items()
        ]
        lines.append(f"| minus {other} | " + " | ".join(cells) + " |")
    return lines


def _fmt(metric: str, value: float) -> str:
    """Accuracy as a percentage, other metrics to three decimals."""
    return f"{value:.1%}" if metric == "accuracy" else f"{value:.3f}"


def _delta(metric: str, value: float) -> str:
    """Signed difference: accuracy in percentage points, others to three decimals."""
    return f"{value * 100:+.1f}" if metric == "accuracy" else f"{value:+.3f}"


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
