"""Dataset metadata model and builder.

Every dataset that passes through the ingestion pipeline produces a
``DatasetMetadata`` record. This record is the audit trail for the dataset:
it captures provenance, integrity, and schema state at the time of ingest.

Metadata records are stored as JSON sidecars next to the raw data files.
"""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field

from shared.constants import CHECKSUM_ALGORITHM, CURRENT_SCHEMA_VERSION
from shared.types import (
    Checksum,
    DatasetName,
    DatasetVersion,
    ProviderId,
    SchemaVersion,
)


class DatasetMetadata(BaseModel):
    """Immutable provenance record for an ingested dataset."""

    provider_id: ProviderId
    dataset_name: DatasetName
    source_url: str
    downloaded_at: datetime
    checksum: Checksum
    checksum_algorithm: str
    schema_version: SchemaVersion
    dataset_version: DatasetVersion
    license: str
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    columns: list[str]

    model_config = {"frozen": True}

    def to_json(self) -> str:
        """Serialise to a JSON string for sidecar storage."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, text: str) -> "DatasetMetadata":
        """Deserialise from a JSON sidecar string."""
        return cls.model_validate_json(text)


def _compute_checksum(content: bytes, algorithm: str = CHECKSUM_ALGORITHM) -> Checksum:
    """Return the hex digest of ``content`` using ``algorithm``."""
    h = hashlib.new(algorithm)
    h.update(content)
    return Checksum(h.hexdigest())


def _dataset_version_from_timestamp(ts: datetime) -> DatasetVersion:
    """Derive a sortable version string from a UTC timestamp."""
    return DatasetVersion(ts.strftime("%Y%m%d_%H%M%S"))


class MetadataBuilder:
    """Constructs ``DatasetMetadata`` from ingestion artefacts.

    Intended to be called by ``DatasetDownloader`` after a successful fetch,
    normalise, and store cycle.
    """

    @staticmethod
    def build(
        *,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        source_url: str,
        raw_content: bytes,
        df: pd.DataFrame,
        license: str,
        schema_version: SchemaVersion = CURRENT_SCHEMA_VERSION,
        downloaded_at: datetime | None = None,
    ) -> DatasetMetadata:
        """Build a ``DatasetMetadata`` record from ingestion inputs.

        Args:
            provider_id: Identifier of the provider that supplied the data.
            dataset_name: Name of the dataset as declared by the provider.
            source_url: Exact URL the content was fetched from.
            raw_content: Undecoded bytes as returned by the HTTP transport.
            df: Normalised DataFrame (used for row/column counts and column names).
            license: Data license string from the provider.
            schema_version: Current schema version (defaults to project constant).
            downloaded_at: Override the download timestamp (defaults to now in UTC).

        Returns:
            Immutable ``DatasetMetadata`` record.
        """
        ts = downloaded_at if downloaded_at is not None else datetime.now(UTC)
        return DatasetMetadata(
            provider_id=provider_id,
            dataset_name=dataset_name,
            source_url=source_url,
            downloaded_at=ts,
            checksum=_compute_checksum(raw_content),
            checksum_algorithm=CHECKSUM_ALGORITHM,
            schema_version=schema_version,
            dataset_version=_dataset_version_from_timestamp(ts),
            license=license,
            row_count=len(df),
            column_count=len(df.columns),
            columns=list(df.columns),
        )

    @staticmethod
    def save(metadata: DatasetMetadata, path: Path) -> None:
        """Write a metadata record to a JSON sidecar file.

        Args:
            metadata: The record to persist.
            path: Destination file path (parent directory must exist).
        """
        path.write_text(metadata.to_json(), encoding="utf-8")

    @staticmethod
    def load(path: Path) -> DatasetMetadata:
        """Load a metadata record from a JSON sidecar file.

        Args:
            path: Path to the JSON sidecar file.

        Returns:
            Deserialised ``DatasetMetadata`` record.

        Raises:
            FileNotFoundError: If ``path`` does not exist.
            ValueError: If the file content is not valid metadata JSON.
        """
        text = path.read_text(encoding="utf-8")
        try:
            return DatasetMetadata.from_json(text)
        except Exception as exc:
            raise ValueError(f"Invalid metadata file at {path}: {exc}") from exc

    @staticmethod
    def verify_checksum(metadata: DatasetMetadata, content: bytes) -> bool:
        """Return True if ``content`` matches the recorded checksum."""
        actual = _compute_checksum(content, metadata.checksum_algorithm)
        return actual == metadata.checksum
