"""Multi-season, multi-league backfill from football-data.co.uk (ADR 005).

``HistoryBackfill`` fetches one CSV per division season, stores each as an
immutable raw partition, canonicalises it, runs season integrity checks and
writes one combined processed file plus a JSON report.

Raw partitions already on disk are reused, so a rerun never re-downloads and
always rebuilds the same combined dataset from the same bytes.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

import pandas as pd

from ingestion.downloader import HttpTransport, HttpxTransport
from ingestion.storage import DatasetStorage
from providers.base import BaseProvider
from schemas.match import MatchNormalizer
from shared.exceptions import IngestionError, ValidationError
from shared.types import DatasetName, DatasetVersion
from validation.dataset_validator import (
    DatasetValidator,
    NullConstraintRule,
    RequiredColumnsRule,
    RowCountRule,
)
from validation.season_integrity import check_season_integrity

SOURCE_DATASET = DatasetName("match_results")
COMBINED_DATASET = DatasetName("match_results_top5")

# Share of rows per season allowed to fail canonical normalisation.
DEFAULT_MAX_FAILED_RATIO = 0.005

_REQUIRED = ["date", "home_team", "away_team", "home_goals_ft", "away_goals_ft"]
_SORT_KEYS = ["match_date", "competition", "home_team"]


@dataclass(frozen=True)
class PlannedFile:
    """One division season the backfill will read."""

    division: str
    season_code: str
    url: str
    cached: bool


@dataclass(frozen=True)
class SeasonOutcome:
    """What the backfill found in one division season."""

    division: str
    season_code: str
    url: str
    checksum: str
    rows: int
    failed_rows: int
    downloaded: bool
    errors: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class BackfillResult:
    """Paths and per-season outcomes of a successful backfill."""

    processed_path: str
    report_path: str
    row_count: int
    seasons: list[SeasonOutcome]


class HistoryBackfill:
    """Builds one validated multi-season dataset from per-season source files."""

    def __init__(
        self,
        provider: BaseProvider,
        storage: DatasetStorage,
        transport: HttpTransport | None = None,
        normalizer: MatchNormalizer | None = None,
        max_failed_ratio: float = DEFAULT_MAX_FAILED_RATIO,
    ) -> None:
        self._provider = provider
        self._storage = storage
        self._transport: HttpTransport = transport or HttpxTransport("football_data")
        self._normalizer = normalizer or MatchNormalizer()
        self._max_failed_ratio = max_failed_ratio

    def plan(self, divisions: list[str], season_codes: list[str]) -> list[PlannedFile]:
        """List every division season in order, marking those already stored."""
        return [
            PlannedFile(
                division=division,
                season_code=season,
                url=self._provider.build_url(
                    SOURCE_DATASET, season=season, division=division
                ),
                cached=self._storage.has_raw_partition(
                    self._provider.provider_id,
                    SOURCE_DATASET,
                    _partition(division, season),
                ),
            )
            for division in divisions
            for season in season_codes
        ]

    def run(self, divisions: list[str], season_codes: list[str]) -> BackfillResult:
        """Fetch, validate and combine every division season.

        Raises:
            IngestionError: If a season has too many unparseable rows.
            ValidationError: If any season fails integrity checks. The report
                is still written so every failure can be inspected at once.
        """
        frames: list[pd.DataFrame] = []
        outcomes: list[SeasonOutcome] = []
        for planned in self.plan(divisions, season_codes):
            frame, outcome = self._process(planned)
            frames.append(frame)
            outcomes.append(outcome)

        version = DatasetVersion(datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S"))
        combined = pd.concat(frames, ignore_index=True).sort_values(
            _SORT_KEYS, kind="stable", ignore_index=True
        )
        report_path = self._storage.save_report(
            _report(outcomes, len(combined), self._provider.license),
            self._provider.provider_id,
            COMBINED_DATASET,
            version,
        )
        errors = [e for o in outcomes for e in o.errors]
        if errors:
            raise ValidationError(str(COMBINED_DATASET), "; ".join(errors))

        processed_path = self._storage.save_dataframe(
            combined, self._provider.provider_id, COMBINED_DATASET, version
        )
        return BackfillResult(
            processed_path=str(processed_path),
            report_path=str(report_path),
            row_count=len(combined),
            seasons=outcomes,
        )

    def _process(self, planned: PlannedFile) -> tuple[pd.DataFrame, SeasonOutcome]:
        """Load or download one season, then canonicalise and check it."""
        content = self._fetch(planned)
        label = f"{planned.division} {planned.season_code}"
        normalised = self._provider.normalise_columns(
            self._provider.parse(content, SOURCE_DATASET)
        )
        _require_columns(normalised, label)
        frame, failed = self._normalizer.normalise_dataframe(
            normalised, season_code=planned.season_code, division=planned.division
        )
        if failed > len(normalised) * self._max_failed_ratio:
            raise IngestionError(
                str(SOURCE_DATASET),
                f"{label}: {failed} of {len(normalised)} rows failed normalisation",
            )
        checks = check_season_integrity(frame, planned.division, planned.season_code)
        return frame, SeasonOutcome(
            division=planned.division,
            season_code=planned.season_code,
            url=planned.url,
            checksum=hashlib.sha256(content).hexdigest(),
            rows=len(frame),
            failed_rows=failed,
            downloaded=not planned.cached,
            errors=checks.errors,
            warnings=checks.warnings,
        )

    def _fetch(self, planned: PlannedFile) -> bytes:
        """Return stored raw bytes, downloading and storing them if missing."""
        partition = _partition(planned.division, planned.season_code)
        provider_id = self._provider.provider_id
        if planned.cached:
            return self._storage.load_raw_partition(
                provider_id, SOURCE_DATASET, partition
            )
        content = self._transport.get(planned.url, timeout=30)
        self._storage.save_raw_partition(
            content, provider_id, SOURCE_DATASET, partition
        )
        return content


def _partition(division: str, season_code: str) -> str:
    """Return the raw partition name for one division season."""
    return f"{division}_{season_code}"


def _require_columns(df: pd.DataFrame, label: str) -> None:
    """Raise ``ValidationError`` if core match columns are missing or null."""
    result = DatasetValidator().validate(
        df,
        [
            RequiredColumnsRule(_REQUIRED),
            NullConstraintRule(_REQUIRED),
            RowCountRule(1),
        ],
    )
    if not result.passed:
        raise ValidationError(label, "; ".join(result.errors))


def _report(
    outcomes: list[SeasonOutcome], rows: int, license: str
) -> dict[str, object]:
    """Build the JSON report describing a backfill run."""
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "license": license,
        "row_count": rows,
        "season_count": len(outcomes),
        "passed": not any(o.errors for o in outcomes),
        "seasons": [asdict(o) for o in outcomes],
    }
