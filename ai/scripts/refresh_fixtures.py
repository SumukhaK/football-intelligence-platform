"""CLI: download the five leagues' upcoming fixtures (ADR 015).

Usage:
    uv run python -m scripts.refresh_fixtures [--base-dir ../datasets] [--confirm]

Without ``--confirm`` the script only prints what it would do. With it, each
league's season schedule is downloaded from openfootball (one raw snapshot
per league per day), and matches not yet played are written as
``processed/openfootball/fixtures_v<timestamp>.csv``. The backend does the
same every day as part of its data refresh; use this script to refresh by
hand, then restart the backend.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from ingestion.fixtures import LEAGUES, refresh_fixtures, season_folder


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="refresh_fixtures")
    parser.add_argument("--base-dir", default="../datasets")
    parser.add_argument(
        "--confirm", action="store_true", help="Download and write (default: dry run)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns 0 on success or dry run, 1 on failure."""
    args = _build_arg_parser().parse_args(argv)
    print(f"Season:  {season_folder(date.today())} ({', '.join(LEAGUES)})")
    if not args.confirm:
        print("Dry run. Re-run with --confirm to download and write.")
        return 0
    try:
        path = refresh_fixtures(Path(args.base_dir), date.today())
    except Exception as exc:  # noqa: BLE001 — surface any failure as exit code 1
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    counts = pd.read_csv(path)["competition"].value_counts()
    for competition in LEAGUES:
        print(f"{competition:<15} {counts.get(competition, 0)} upcoming")
    print(f"Written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
