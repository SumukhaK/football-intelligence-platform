"""Rebuild the served live dataset: completed history plus the season so far.

Used by ``scripts.refresh_live_dataset`` and by the backend's daily refresh
(ADR 013). Each division's in-progress file is stored once per day as an
immutable raw partition, so refreshing twice on one day reuses that day's
download.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd

from config.leagues import TOP_FIVE_DIVISIONS
from config.paths import DataPaths
from ingestion.downloader import HttpTransport, HttpxTransport
from ingestion.in_progress import combine_with_history, fetch_in_progress
from ingestion.storage import DatasetStorage
from providers.football_data import FootballDataProvider
from shared.types import DatasetName, DatasetVersion

LIVE_DATASET = DatasetName("match_results_live")
_VERSION = re.compile(r"_v(\d{8}_\d{6})\.csv$")


def season_code_for(day: date) -> str:
    """Four-digit season code for a date; seasons start on 1 July.

    Example: 29 September 2026 → ``"2627"``.
    """
    start = day.year if day.month >= 7 else day.year - 1
    return f"{start % 100:02d}{(start + 1) % 100:02d}"


def refresh_live_dataset(
    base_dir: Path,
    as_of: date,
    divisions: list[str] | None = None,
    transport: HttpTransport | None = None,
    season_code: str | None = None,
) -> Path:
    """Download the season in progress and write a new live dataset.

    ``season_code`` defaults to the season ``as_of`` falls in.

    Raises:
        FileNotFoundError: If no completed-season dataset exists yet.
        IngestionError, ValidationError: If a download or its checks fail.
    """
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
        provider,
        storage,
        transport or HttpxTransport(),
        divisions or list(TOP_FIVE_DIVISIONS),
        season_code or season_code_for(as_of),
        as_of,
    )
    version = DatasetVersion(datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S"))
    return storage.save_dataframe(
        combine_with_history(history, current),
        provider.provider_id,
        LIVE_DATASET,
        version,
    )


def dataset_built_at(path: Path) -> datetime | None:
    """UTC time a versioned dataset was written, read from its file name."""
    match = _VERSION.search(path.name)
    if match is None:
        return None
    return datetime.strptime(match.group(1), "%Y%m%d_%H%M%S").replace(tzinfo=UTC)
