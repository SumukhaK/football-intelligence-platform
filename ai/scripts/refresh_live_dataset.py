"""CLI: refresh the served match dataset with a season in progress (ADR 008).

Usage:
    uv run python -m scripts.refresh_live_dataset [--season 2627]
        [--divisions E0 D1 SP1 I1 F1] [--base-dir ../datasets] [--confirm]

Without ``--confirm`` the script only prints what it would do. With it, the
season's played matches are downloaded (one raw snapshot per division per
day), appended to the newest completed-season dataset, and written as
``processed/football_data/match_results_live_v<timestamp>.csv``. The backend
loads the newest live dataset at startup; restart it to pick up a refresh.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd

from config.leagues import TOP_FIVE_DIVISIONS
from config.paths import DataPaths
from ingestion.downloader import HttpxTransport
from ingestion.in_progress import combine_with_history, fetch_in_progress
from ingestion.storage import DatasetStorage
from providers.football_data import FootballDataProvider
from schemas.match import season_label
from shared.types import DatasetName, DatasetVersion

LIVE_DATASET = DatasetName("match_results_live")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="refresh_live_dataset")
    parser.add_argument("--season", default="2627", help="Season code, e.g. 2627")
    parser.add_argument("--divisions", nargs="+", default=list(TOP_FIVE_DIVISIONS))
    parser.add_argument("--base-dir", default="../datasets")
    parser.add_argument(
        "--confirm", action="store_true", help="Download and write (default: dry run)"
    )
    return parser


def refresh(base_dir: Path, divisions: list[str], season_code: str) -> Path:
    """Download the season so far and write the combined live dataset."""
    provider = FootballDataProvider()
    storage = DatasetStorage(DataPaths(base_dir=base_dir))
    history_files = sorted(
        (base_dir / "processed" / provider.provider_id).glob(
            "match_results_top5_v*.csv"
        )
    )
    if not history_files:
        raise FileNotFoundError("No match_results_top5 dataset; run the backfill")
    history = pd.read_csv(history_files[-1])
    current = fetch_in_progress(
        provider, storage, HttpxTransport(), divisions, season_code, date.today()
    )
    version = DatasetVersion(datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S"))
    return storage.save_dataframe(
        combine_with_history(history, current),
        provider.provider_id,
        LIVE_DATASET,
        version,
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns 0 on success or dry run, 1 on failure."""
    args = _build_arg_parser().parse_args(argv)
    print(f"Season:    {season_label(args.season)} ({' '.join(args.divisions)})")
    if not args.confirm:
        print("Dry run. Re-run with --confirm to download and write.")
        return 0
    try:
        path = refresh(Path(args.base_dir), args.divisions, args.season)
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
