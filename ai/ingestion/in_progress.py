"""Download the played matches of a season still in progress.

Each division's file is stored as an immutable raw partition named with the
download date, so everything built from it on that day is reproducible. Rows
are checked with the partial-season rules (ADR 006): no match counts, but no
duplicate fixtures, inconsistent results or dates outside the season.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from ingestion.downloader import HttpTransport
from ingestion.storage import DatasetStorage
from providers.base import BaseProvider
from schemas.match import MatchNormalizer, ProcessedMatch
from shared.exceptions import IngestionError, ValidationError
from shared.types import DatasetName
from validation.season_integrity import check_partial_season

IN_PROGRESS_DATASET = DatasetName("match_results_in_progress")
_SOURCE_DATASET = DatasetName("match_results")
_PLAYED = ["home_goals_ft", "away_goals_ft", "result_ft"]
_CANONICAL_COLUMNS = list(ProcessedMatch.model_fields)


def fetch_in_progress(
    provider: BaseProvider,
    storage: DatasetStorage,
    transport: HttpTransport,
    divisions: list[str],
    season_code: str,
    as_of: date,
) -> pd.DataFrame:
    """Return canonical played matches of a season in progress.

    Each division's file is stored as an immutable raw partition named with
    ``as_of``, so a rerun on the same day scores the same results.

    Raises:
        ValidationError: If a division fails the partial-season checks.
        IngestionError: If any played row cannot be canonicalised.
    """
    frames = []
    for division in divisions:
        content = _load_or_download(
            provider, storage, transport, division, season_code, as_of
        )
        frames.append(_canonical(provider, content, division, season_code))
    return pd.concat(frames, ignore_index=True)


def _load_or_download(
    provider: BaseProvider,
    storage: DatasetStorage,
    transport: HttpTransport,
    division: str,
    season_code: str,
    as_of: date,
) -> bytes:
    """Return the stored snapshot for ``as_of``, downloading it if missing."""
    partition = f"{division}_{season_code}_{as_of:%Y%m%d}"
    pid = provider.provider_id
    if storage.has_raw_partition(pid, IN_PROGRESS_DATASET, partition):
        return storage.load_raw_partition(pid, IN_PROGRESS_DATASET, partition)
    url = provider.build_url(_SOURCE_DATASET, season=season_code, division=division)
    content = transport.get(url, timeout=30)
    storage.save_raw_partition(content, pid, IN_PROGRESS_DATASET, partition)
    return content


def _canonical(
    provider: BaseProvider, content: bytes, division: str, season_code: str
) -> pd.DataFrame:
    """Parse one division file, keep played matches and validate them."""
    label = f"{division} {season_code}"
    normalised = provider.normalise_columns(provider.parse(content, _SOURCE_DATASET))
    played = normalised.dropna(subset=_PLAYED)
    if played.empty:
        # Early in a season a league may not have played yet.
        return pd.DataFrame(columns=_CANONICAL_COLUMNS)
    frame, failed = MatchNormalizer().normalise_dataframe(
        played, season_code=season_code, division=division
    )
    if failed:
        raise IngestionError(str(IN_PROGRESS_DATASET), f"{label}: {failed} bad rows")
    checks = check_partial_season(frame, division, season_code)
    if not checks.passed:
        raise ValidationError(label, "; ".join(checks.errors))
    return frame


def combine_with_history(history: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    """Append an in-progress season to completed history, sorted by date.

    Raises:
        ValidationError: If the in-progress season is already in the history.
    """
    overlap = sorted(set(history["season"]) & set(current["season"]))
    if overlap:
        raise ValidationError(
            str(IN_PROGRESS_DATASET), f"Seasons already in history: {overlap}"
        )
    combined = pd.concat([history, current], ignore_index=True)
    combined["match_date"] = combined["match_date"].astype(str)
    return combined.sort_values(
        ["match_date", "competition", "home_team"], kind="stable", ignore_index=True
    )
