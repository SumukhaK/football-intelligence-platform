"""CLI: download and ingest football-data.co.uk match results.

Usage:
    uv run python -m scripts.ingest_football_data [--season SEASON] [--division DIV]

Defaults to the 2023/24 Premier League (--season 2324 --division E0).

All output paths are printed on completion. Set FOOTBALL_AI_DATASETS_BASE_DIR
in the environment or .env to control where files are written.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ingest_football_data",
        description="Ingest football match data from football-data.co.uk",
    )
    parser.add_argument(
        "--season",
        default="2324",
        help="Four-digit season code, e.g. 2324 for 2023/24 (default: 2324)",
    )
    parser.add_argument(
        "--division",
        default="E0",
        help="Division code, e.g. E0=Premier League, E1=Championship (default: E0)",
    )
    parser.add_argument(
        "--base-dir",
        default=None,
        help="Override datasets base directory (default: from settings or datasets/)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns exit code 0 on success, 1 on failure."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    from config.paths import DataPaths
    from config.settings import get_settings
    from ingestion.pipeline import IngestionPipeline
    from ingestion.storage import DatasetStorage
    from providers.football_data import FootballDataProvider
    from schemas.match import DIVISION_TO_COMPETITION, season_label
    from shared.types import DatasetName

    settings = get_settings()
    base_dir = Path(args.base_dir) if args.base_dir else settings.datasets_base_dir
    paths = DataPaths(base_dir=base_dir)
    paths.ensure_all()

    season = args.season
    division = args.division
    competition = DIVISION_TO_COMPETITION.get(division, division)

    print("Football Intelligence Platform — Data Ingestion")
    print("=" * 48)
    print("Provider:    football-data.co.uk")
    print(f"Competition: {competition}")
    print(f"Season:      {season_label(season)}")
    print(f"Output dir:  {base_dir}")
    print()

    provider = FootballDataProvider()
    storage = DatasetStorage(paths)
    pipeline = IngestionPipeline(provider=provider, storage=storage)
    dataset_name = DatasetName("match_results")

    print("Downloading...", end=" ", flush=True)
    start = time.monotonic()
    try:
        result = pipeline.run(dataset_name, season_code=season, division=division)
    except Exception as exc:
        print(f"FAILED\n\nError: {exc}", file=sys.stderr)
        return 1
    elapsed = time.monotonic() - start

    print(f"Done ({elapsed:.1f}s)")
    print()
    print(f"Rows ingested:  {result.row_count}")
    if result.failed_rows:
        print(f"Rows skipped:   {result.failed_rows} (failed canonical normalisation)")
    print()
    print(f"Raw dataset:    {result.raw_path}")
    print(f"Processed:      {result.processed_path}")
    print(f"Metadata:       {result.metadata_path}")
    print(f"Version:        {result.dataset_version}")
    print(f"Checksum:       {result.checksum}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
