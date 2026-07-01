"""Abstract base class for football data providers.

The provider is responsible for three things only:
1. Declaring which datasets it can supply (``available_datasets``).
2. Building the download URL for a named dataset (``build_url``).
3. Parsing raw bytes into a normalised DataFrame (``parse`` + ``normalise_columns``).

HTTP transport and persistence are handled by ``DatasetDownloader`` and
``DatasetStorage`` respectively, so providers remain testable without a network.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from shared.exceptions import DatasetNotFoundError
from shared.types import DatasetName, ProviderId


@dataclass(frozen=True)
class DatasetDescriptor:
    """Describes a dataset that a provider can supply."""

    name: DatasetName
    description: str
    url_template: str
    license: str
    default_params: dict[str, str]


class BaseProvider(ABC):
    """Abstract base for all football data providers.

    Subclasses must implement every abstract method. The concrete methods
    (``get_descriptor``) may be used directly.
    """

    @property
    @abstractmethod
    def provider_id(self) -> ProviderId:
        """Stable machine-readable identifier, e.g. ``ProviderId("football_data")``."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name shown in logs and metadata."""

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Root URL for this provider's data portal."""

    @property
    @abstractmethod
    def license(self) -> str:
        """Data license identifier, e.g. ``"CC BY 4.0"``."""

    @abstractmethod
    def available_datasets(self) -> list[DatasetDescriptor]:
        """Return all datasets this provider can supply."""

    @abstractmethod
    def build_url(self, dataset_name: DatasetName, **params: str) -> str:
        """Construct the download URL for a named dataset.

        Args:
            dataset_name: Name of the dataset as returned by ``available_datasets``.
            **params: Provider-specific URL parameters (season, league, etc.).

        Returns:
            Fully-qualified download URL.

        Raises:
            DatasetNotFoundError: If ``dataset_name`` is not in ``available_datasets``.
        """

    @abstractmethod
    def parse(self, content: bytes, dataset_name: DatasetName) -> pd.DataFrame:
        """Parse raw downloaded bytes into a DataFrame with provider-native columns.

        Args:
            content: Raw bytes as returned by the HTTP transport.
            dataset_name: Name of the dataset being parsed.

        Returns:
            DataFrame with provider-native column names (before normalisation).

        Raises:
            IngestionError: If ``content`` cannot be parsed.
        """

    @abstractmethod
    def normalise_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename provider-specific columns to platform-standard names.

        The platform standard uses lowercase snake_case. Columns that have no
        platform equivalent are dropped.

        Args:
            df: DataFrame with provider-native column names.

        Returns:
            DataFrame with platform-standard column names.
        """

    def get_descriptor(self, dataset_name: DatasetName) -> DatasetDescriptor:
        """Return the descriptor for a named dataset.

        Raises:
            DatasetNotFoundError: If ``dataset_name`` is not known to this provider.
        """
        for descriptor in self.available_datasets():
            if descriptor.name == dataset_name:
                return descriptor
        raise DatasetNotFoundError(
            str(self.provider_id),
            f"Unknown dataset '{dataset_name}'. "
            f"Available: {[d.name for d in self.available_datasets()]}",
        )
