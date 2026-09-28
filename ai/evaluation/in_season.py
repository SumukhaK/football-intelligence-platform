"""Score the served model on a season in progress, match by match.

Each played match of the season is predicted with features built only from
matches before it: the in-progress results are appended to the completed
history and run through the same feature pipeline used for training. The model
is not retrained, so every prediction is genuinely out of sample.

The command-line entry point is ``evaluation.in_season_cli``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from evaluation.compare_models import score_block
from evaluation.comparison import class_prior_probabilities
from feature_engineering.pipeline import FeaturePipeline
from ingestion.downloader import HttpTransport
from ingestion.storage import DatasetStorage
from providers.base import BaseProvider
from schemas.match import MatchNormalizer
from shared.exceptions import IngestionError, ValidationError
from shared.types import DatasetName
from validation.season_integrity import check_partial_season

IN_PROGRESS_DATASET = DatasetName("match_results_in_progress")
_SOURCE_DATASET = DatasetName("match_results")
_PLAYED = ["home_goals_ft", "away_goals_ft", "result_ft"]


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
    frame, failed = MatchNormalizer().normalise_dataframe(
        played, season_code=season_code, division=division
    )
    if failed:
        raise IngestionError(str(IN_PROGRESS_DATASET), f"{label}: {failed} bad rows")
    checks = check_partial_season(frame, division, season_code)
    if not checks.passed:
        raise ValidationError(label, "; ".join(checks.errors))
    return frame


def build_season_features(
    history: pd.DataFrame, current: pd.DataFrame, work_dir: Path
) -> pd.DataFrame:
    """Run the feature pipeline over history plus the current season.

    Returns only the current season's rows, each with features computed from
    matches before it.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    combined_path = work_dir / "matches_with_current_season.csv"
    pd.concat([history, current], ignore_index=True).to_csv(combined_path, index=False)
    FeaturePipeline().run(combined_path, work_dir / "features")
    matrix = pd.read_parquet(work_dir / "features" / "feature_matrix.parquet")
    seasons = set(current["season"])
    return matrix[matrix["season"].isin(seasons)].reset_index(drop=True)


def evaluate_season(
    rows: pd.DataFrame, probs: np.ndarray, history: pd.DataFrame, classes: list[str]
) -> dict[str, Any]:
    """Score model, outcome-frequency priors and bookmakers per league."""
    priors = class_prior_probabilities(history["result"], len(rows), classes)
    return score_block(rows, {"candidate": probs, "priors": priors}, classes)


def match_predictions(
    rows: pd.DataFrame, probs: np.ndarray, classes: list[str]
) -> pd.DataFrame:
    """Return one line per match: teams, probabilities, pick and actual result."""
    table = rows[["match_date", "competition", "home_team", "away_team"]].copy()
    for i, cls in enumerate(classes):
        table[f"p_{cls}"] = probs[:, i].round(3)
    table["predicted"] = np.asarray(classes)[probs.argmax(axis=1)]
    table["actual"] = rows["result"].to_numpy()
    table["correct"] = table["predicted"] == table["actual"]
    return table.sort_values(["match_date", "competition", "home_team"])
