"""Dataset storage: reads and writes raw bytes, DataFrames, and metadata sidecars.

The storage layer owns the on-disk layout. Nothing else in the pipeline
constructs file paths or opens files directly.

Directory layout under ``DataPaths.raw``:
    raw/
      {provider_id}/
        {dataset_name}_v{version}.csv          # raw bytes as-received
        {dataset_name}_v{version}_metadata.json

Directory layout under ``DataPaths.processed``:
    processed/
      {provider_id}/
        {dataset_name}_v{version}.csv          # normalised DataFrame
"""

from pathlib import Path

import pandas as pd

from config.paths import DataPaths
from metadata.metadata import DatasetMetadata, MetadataBuilder
from shared.constants import DATASET_VERSION_SEPARATOR
from shared.exceptions import StorageError
from shared.types import DatasetName, DatasetVersion, ProviderId


def _raw_filename(dataset_name: DatasetName, version: DatasetVersion) -> str:
    return f"{dataset_name}{DATASET_VERSION_SEPARATOR}{version}.csv"


def _processed_filename(dataset_name: DatasetName, version: DatasetVersion) -> str:
    return f"{dataset_name}{DATASET_VERSION_SEPARATOR}{version}.csv"


def _metadata_filename(dataset_name: DatasetName, version: DatasetVersion) -> str:
    return f"{dataset_name}{DATASET_VERSION_SEPARATOR}{version}_metadata.json"


class DatasetStorage:
    """File-system storage for raw bytes, normalised DataFrames, and metadata.

    Args:
        paths: Configured data path layout.
    """

    def __init__(self, paths: DataPaths) -> None:
        self._paths = paths

    def save_raw(
        self,
        content: bytes,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        version: DatasetVersion,
    ) -> Path:
        """Persist raw downloaded bytes under ``raw/{provider_id}/``.

        Args:
            content: Raw bytes as returned by the HTTP transport.
            provider_id: Provider that supplied the content.
            dataset_name: Dataset name.
            version: Dataset version string (timestamp-derived).

        Returns:
            Absolute path to the written file.
        """
        target_dir = self._paths.provider_raw_dir(provider_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / _raw_filename(dataset_name, version)
        try:
            path.write_bytes(content)
        except OSError as exc:
            raise StorageError(f"Failed to write raw file '{path}': {exc}") from exc
        return path

    def load_raw(
        self,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        version: DatasetVersion,
    ) -> bytes:
        """Read raw bytes for a previously stored dataset version.

        Raises:
            StorageError: If the file does not exist.
        """
        path = self._paths.provider_raw_dir(provider_id) / _raw_filename(
            dataset_name, version
        )
        if not path.exists():
            raise StorageError(
                f"Raw file not found: '{path}'. "
                f"Has '{dataset_name}' version '{version}' been downloaded?"
            )
        return path.read_bytes()

    def save_dataframe(
        self,
        df: pd.DataFrame,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        version: DatasetVersion,
    ) -> Path:
        """Persist a normalised DataFrame under ``processed/{provider_id}/``.

        Returns:
            Absolute path to the written CSV file.
        """
        target_dir = self._paths.processed / provider_id
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / _processed_filename(dataset_name, version)
        try:
            df.to_csv(path, index=False, encoding="utf-8")
        except OSError as exc:
            raise StorageError(
                f"Failed to write processed file '{path}': {exc}"
            ) from exc
        return path

    def load_dataframe(
        self,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        version: DatasetVersion,
    ) -> pd.DataFrame:
        """Load a normalised DataFrame from the processed store.

        Raises:
            StorageError: If the file does not exist.
        """
        path = (
            self._paths.processed
            / provider_id
            / _processed_filename(dataset_name, version)
        )
        if not path.exists():
            raise StorageError(
                f"Processed file not found: '{path}'. "
                f"Has '{dataset_name}' version '{version}' been ingested?"
            )
        return pd.read_csv(path, encoding="utf-8")

    def save_metadata(
        self,
        metadata: DatasetMetadata,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        version: DatasetVersion,
    ) -> Path:
        """Write a metadata sidecar alongside the raw file.

        Returns:
            Absolute path to the written JSON sidecar.
        """
        target_dir = self._paths.provider_raw_dir(provider_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / _metadata_filename(dataset_name, version)
        MetadataBuilder.save(metadata, path)
        return path

    def load_metadata(
        self,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        version: DatasetVersion,
    ) -> DatasetMetadata:
        """Load a metadata sidecar for a stored dataset version.

        Raises:
            StorageError: If the sidecar file does not exist.
        """
        path = self._paths.provider_raw_dir(provider_id) / _metadata_filename(
            dataset_name, version
        )
        if not path.exists():
            raise StorageError(f"Metadata sidecar not found: '{path}'.")
        return MetadataBuilder.load(path)

    def list_versions(
        self,
        provider_id: ProviderId,
        dataset_name: DatasetName,
    ) -> list[DatasetVersion]:
        """Return all stored versions for a dataset, sorted oldest first."""
        target_dir = self._paths.provider_raw_dir(provider_id)
        if not target_dir.exists():
            return []
        prefix = f"{dataset_name}{DATASET_VERSION_SEPARATOR}"
        versions = []
        for path in target_dir.glob(f"{prefix}*.csv"):
            stem = path.stem  # e.g. "match_results_v20240101_120000"
            version_str = stem[len(prefix) :]
            versions.append(DatasetVersion(version_str))
        return sorted(versions)
