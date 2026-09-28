"""CLI: backfill top-five league history from football-data.co.uk (ADR 005).

Usage:
    uv run python -m scripts.backfill_football_data [--divisions E0 D1 ...]
        [--first-season 0001] [--last-season 2526] [--base-dir DIR] [--confirm]

Without ``--confirm`` the script only prints what it would download. With it,
missing season files are downloaded into ``raw/football_data/match_results/``,
existing ones are reused, and a combined ``match_results_top5`` dataset plus a
JSON report are written to ``processed/football_data/``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config.leagues import TOP_FIVE_DIVISIONS, season_codes


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="backfill_football_data",
        description="Backfill multi-season league results from football-data.co.uk",
    )
    parser.add_argument(
        "--divisions",
        nargs="+",
        default=list(TOP_FIVE_DIVISIONS),
        help="Division codes (default: E0 D1 SP1 I1 F1)",
    )
    parser.add_argument("--first-season", default="0001", help="Default: 0001")
    parser.add_argument("--last-season", default="2526", help="Default: 2526")
    parser.add_argument(
        "--base-dir",
        default=None,
        help="Override datasets base directory (default: from settings)",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Download missing files and build the dataset (default: dry run)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns 0 on success or dry run, 1 on failure."""
    args = _build_arg_parser().parse_args(argv)

    from config.paths import DataPaths
    from config.settings import get_settings
    from ingestion.backfill import HistoryBackfill
    from ingestion.storage import DatasetStorage
    from providers.football_data import FootballDataProvider

    settings = get_settings()
    base_dir = Path(args.base_dir) if args.base_dir else settings.datasets_base_dir
    paths = DataPaths(base_dir=base_dir)
    paths.ensure_all()
    backfill = HistoryBackfill(FootballDataProvider(), DatasetStorage(paths))

    seasons = season_codes(args.first_season, args.last_season)
    plan = backfill.plan(args.divisions, seasons)
    to_download = [p for p in plan if not p.cached]
    print(f"Divisions: {' '.join(args.divisions)}")
    print(f"Seasons:   {seasons[0]} to {seasons[-1]} ({len(seasons)})")
    print(f"Files:     {len(plan)} ({len(to_download)} to download)")
    print(f"Output:    {base_dir}")
    if not args.confirm:
        print("\nDry run. Re-run with --confirm to download and build.")
        return 0

    try:
        result = backfill.run(args.divisions, seasons)
    except Exception as exc:  # noqa: BLE001 — surface any failure as exit code 1
        print(f"\nFAILED: {exc}", file=sys.stderr)
        return 1

    print(f"\nRows:      {result.row_count}")
    for outcome in result.seasons:
        for warning in outcome.warnings:
            print(f"WARN:      {warning}")
    print(f"Processed: {result.processed_path}")
    print(f"Report:    {result.report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
