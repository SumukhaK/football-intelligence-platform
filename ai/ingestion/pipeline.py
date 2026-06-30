"""End-to-end ingestion pipeline for a single provider dataset.

``IngestionPipeline`` orchestrates all steps from raw download to canonical
processed output:

1. Build URL from provider and parameters.
2. Download raw bytes via injected HTTP transport.
3. Parse bytes to DataFrame via provider.
4. Validate normalised DataFrame with composable rules.
5. Canonicalise rows to ``ProcessedMatch`` schema.
6. Persist raw bytes, canonical DataFrame, and metadata sidecar.
7. Return a ``PipelineResult`` describing every output.

Unlike ``DatasetDownloader`` (which saves the intermediate normalised form),
this pipeline saves the canonical ``ProcessedMatch`` DataFrame to
``processed/`` so it is immediately ready for the modelling layer.
"""

from __future__ import annotations

from dataclasses import dataclass

from ingestion.downloader import HttpTransport, HttpxTransport
from ingestion.storage import DatasetStorage
from metadata.metadata import MetadataBuilder
from providers.base import BaseProvider
from schemas.match import DIVISION_TO_COMPETITION, MatchNormalizer, season_label
from shared.constants import CURRENT_SCHEMA_VERSION
from shared.exceptions import IngestionError, ValidationError
from shared.types import DatasetName, DatasetVersion
from validation.dataset_validator import (
    DatasetValidator,
    NullConstraintRule,
    RequiredColumnsRule,
    RowCountRule,
    ValidationRule,
)

_REQUIRED_COLUMNS = [
    "date",
    "home_team",
    "away_team",
    "home_goals_ft",
    "away_goals_ft",
    "result_ft",
]

_BASE_RULES: list[ValidationRule] = [
    RequiredColumnsRule(_REQUIRED_COLUMNS),
    NullConstraintRule(_REQUIRED_COLUMNS),
    RowCountRule(min_rows=1),
]


@dataclass(frozen=True)
class PipelineResult:
    """Outcome of a completed ingestion pipeline run."""

    raw_path: str
    processed_path: str
    metadata_path: str
    row_count: int
    failed_rows: int
    season: str
    division: str
    competition: str
    dataset_version: DatasetVersion
    checksum: str


class IngestionPipeline:
    """Orchestrates download → validate → canonicalise → store for one dataset.

    Args:
        provider: Provider that builds URLs and parses raw bytes.
        storage: Storage backend for all output files.
        transport: HTTP transport (defaults to ``HttpxTransport``).
        normalizer: Row normalizer (defaults to ``MatchNormalizer``).
        validator: Dataset validator (defaults to ``DatasetValidator``).
    """

    def __init__(
        self,
        provider: BaseProvider,
        storage: DatasetStorage,
        transport: HttpTransport | None = None,
        normalizer: MatchNormalizer | None = None,
        validator: DatasetValidator | None = None,
    ) -> None:
        self._provider = provider
        self._storage = storage
        self._transport: HttpTransport = transport or HttpxTransport()
        self._normalizer = normalizer or MatchNormalizer()
        self._validator = validator or DatasetValidator()

    def run(
        self,
        dataset_name: DatasetName,
        *,
        season_code: str,
        division: str,
        extra_rules: list[ValidationRule] | None = None,
    ) -> PipelineResult:
        """Execute the full ingestion pipeline for one dataset.

        Args:
            dataset_name: Dataset name as declared by the provider.
            season_code: Four-digit season code, e.g. ``"2324"``.
            division: Provider division code, e.g. ``"E0"``.
            extra_rules: Additional validation rules appended to the defaults.

        Returns:
            ``PipelineResult`` with paths, row counts, and metadata.

        Raises:
            ValidationError: If the downloaded data fails quality checks.
            IngestionError: If all rows fail canonical normalisation.
        """
        url = self._provider.build_url(
            dataset_name, season=season_code, division=division
        )
        raw_bytes = self._transport.get(url, timeout=30)

        df_raw = self._provider.parse(raw_bytes, dataset_name)
        df_normalised = self._provider.normalise_columns(df_raw)

        rules: list[ValidationRule] = list(_BASE_RULES) + (extra_rules or [])
        validation = self._validator.validate(df_normalised, rules)
        if not validation.passed:
            raise ValidationError(
                str(dataset_name),
                "; ".join(validation.errors),
            )

        df_canonical, failed_rows = self._normalizer.normalise_dataframe(
            df_normalised, season_code=season_code, division=division
        )

        if df_canonical.empty and len(df_normalised) > 0:
            raise IngestionError(
                str(dataset_name),
                f"All {len(df_normalised)} rows failed canonical normalisation",
            )

        metadata = MetadataBuilder.build(
            provider_id=self._provider.provider_id,
            dataset_name=dataset_name,
            source_url=url,
            raw_content=raw_bytes,
            df=df_canonical,
            license=self._provider.license,
            schema_version=CURRENT_SCHEMA_VERSION,
        )

        raw_path = self._storage.save_raw(
            content=raw_bytes,
            provider_id=self._provider.provider_id,
            dataset_name=dataset_name,
            version=metadata.dataset_version,
        )
        processed_path = self._storage.save_dataframe(
            df=df_canonical,
            provider_id=self._provider.provider_id,
            dataset_name=dataset_name,
            version=metadata.dataset_version,
        )
        metadata_path = self._storage.save_metadata(
            metadata=metadata,
            provider_id=self._provider.provider_id,
            dataset_name=dataset_name,
            version=metadata.dataset_version,
        )

        competition = DIVISION_TO_COMPETITION.get(division, division)
        return PipelineResult(
            raw_path=str(raw_path),
            processed_path=str(processed_path),
            metadata_path=str(metadata_path),
            row_count=len(df_canonical),
            failed_rows=failed_rows,
            season=season_label(season_code),
            division=division,
            competition=competition,
            dataset_version=metadata.dataset_version,
            checksum=metadata.checksum,
        )
