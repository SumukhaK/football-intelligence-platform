"""Dataset downloader: orchestrates provider fetch, validation, and storage.

The downloader is the pipeline coordinator. It:
1. Asks the provider to build the download URL.
2. Fetches raw bytes via the HTTP transport.
3. Asks the provider to parse and normalise the bytes into a DataFrame.
4. Builds a metadata record.
5. Persists raw bytes and the normalised DataFrame via DatasetStorage.

The HTTP transport is injected so tests can supply a ``FakeTransport``
without touching the network.
"""

from dataclasses import dataclass
from typing import Protocol

import pandas as pd

from config.settings import Settings, get_settings
from ingestion.storage import DatasetStorage
from metadata.metadata import DatasetMetadata, MetadataBuilder
from providers.base import BaseProvider
from shared.exceptions import IngestionError
from shared.types import DatasetName


class HttpTransport(Protocol):
    """Protocol for HTTP GET transport used by the downloader."""

    def get(self, url: str, timeout: int) -> bytes:
        """Perform a GET request and return the raw response body.

        Args:
            url: Fully-qualified URL to fetch.
            timeout: Request timeout in seconds.

        Returns:
            Raw response bytes.

        Raises:
            IngestionError: On any HTTP or network error.
        """
        ...


class HttpxTransport:
    """Production HTTP transport backed by httpx."""

    def get(self, url: str, timeout: int) -> bytes:
        """Perform a synchronous GET request via httpx."""
        import httpx

        try:
            response = httpx.get(url, timeout=timeout, follow_redirects=True)
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as exc:
            raise IngestionError(
                url, f"HTTP {exc.response.status_code}: {exc.response.reason_phrase}"
            ) from exc
        except httpx.RequestError as exc:
            raise IngestionError(url, f"Request failed: {exc}") from exc


@dataclass
class DownloadResult:
    """The outputs of a completed dataset download cycle."""

    df: pd.DataFrame
    metadata: DatasetMetadata
    raw_path: str
    dataset_path: str


class DatasetDownloader:
    """Coordinates download, parsing, validation, and persistence of a dataset.

    Args:
        provider: Provider that knows how to build URLs and parse responses.
        storage: Storage backend for raw bytes and normalised DataFrames.
        transport: HTTP transport used to fetch raw bytes.
        settings: Application settings (timeout, retries, etc.).
    """

    def __init__(
        self,
        provider: BaseProvider,
        storage: DatasetStorage,
        transport: HttpTransport | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._provider = provider
        self._storage = storage
        self._transport = transport if transport is not None else HttpxTransport()
        self._settings = settings if settings is not None else get_settings()

    def fetch(
        self,
        dataset_name: DatasetName,
        **url_params: str,
    ) -> DownloadResult:
        """Download, parse, store, and return a dataset.

        Args:
            dataset_name: Dataset to fetch as declared by the provider.
            **url_params: Provider-specific URL parameters (season, league, etc.).

        Returns:
            ``DownloadResult`` containing the DataFrame, metadata, and file paths.

        Raises:
            DatasetNotFoundError: If ``dataset_name`` is unknown to the provider.
            IngestionError: If the download or parse step fails.
        """
        descriptor = self._provider.get_descriptor(dataset_name)
        url = self._provider.build_url(dataset_name, **url_params)

        try:
            content = self._transport.get(
                url, timeout=self._settings.http_timeout_seconds
            )
        except IngestionError:
            raise
        except Exception as exc:
            raise IngestionError(
                dataset_name, f"Unexpected error during fetch: {exc}"
            ) from exc

        df_raw = self._provider.parse(content, dataset_name)
        df = self._provider.normalise_columns(df_raw)

        metadata = MetadataBuilder.build(
            provider_id=self._provider.provider_id,
            dataset_name=dataset_name,
            source_url=url,
            raw_content=content,
            df=df,
            license=descriptor.license,
        )

        raw_path = self._storage.save_raw(
            content=content,
            provider_id=self._provider.provider_id,
            dataset_name=dataset_name,
            version=metadata.dataset_version,
        )
        dataset_path = self._storage.save_dataframe(
            df=df,
            provider_id=self._provider.provider_id,
            dataset_name=dataset_name,
            version=metadata.dataset_version,
        )
        self._storage.save_metadata(
            metadata=metadata,
            provider_id=self._provider.provider_id,
            dataset_name=dataset_name,
            version=metadata.dataset_version,
        )

        return DownloadResult(
            df=df,
            metadata=metadata,
            raw_path=str(raw_path),
            dataset_path=str(dataset_path),
        )
