"""CLI: refresh the served match dataset with a season in progress (ADR 008).

Usage:
    uv run python -m scripts.refresh_live_dataset [--season 2627]
        [--divisions E0 D1 SP1 I1 F1] [--base-dir ../datasets] [--confirm]

Without ``--confirm`` the script only prints what it would do. With it, the
season's played matches are downloaded (one raw snapshot per division per
day), appended to the newest completed-season dataset, and written as
``processed/football_data/match_results_live_v<timestamp>.csv``. The backend
does the same refresh itself every day (ADR 013); use this script to refresh
by hand.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from config.leagues import TOP_FIVE_DIVISIONS
from ingestion.live_refresh import refresh_live_dataset, season_code_for
from schemas.match import season_label


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="refresh_live_dataset")
    parser.add_argument(
        "--season",
        default=None,
        help="Season code, e.g. 2627 (default: the season today falls in)",
    )
    parser.add_argument("--divisions", nargs="+", default=list(TOP_FIVE_DIVISIONS))
    parser.add_argument("--base-dir", default="../datasets")
    parser.add_argument(
        "--confirm", action="store_true", help="Download and write (default: dry run)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns 0 on success or dry run, 1 on failure."""
    args = _build_arg_parser().parse_args(argv)
    args.season = args.season or season_code_for(date.today())
    print(f"Season:    {season_label(args.season)} ({' '.join(args.divisions)})")
    if not args.confirm:
        print("Dry run. Re-run with --confirm to download and write.")
        return 0
    try:
        path = refresh_live_dataset(
            Path(args.base_dir), date.today(), args.divisions, season_code=args.season
        )
    except Exception as exc:  # noqa: BLE001 — surface any failure as exit code 1
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    rows = pd.read_csv(path)
    current = rows[rows["season"] == season_label(args.season)]
    print(f"Matches:   {len(current)} played so far, {len(rows)} in total")
    print(f"Last date: {current['match_date'].max()}")
    print(f"Written:   {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
