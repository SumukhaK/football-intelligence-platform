"""Tests for the BaseProvider interface contract."""

import pandas as pd
import pytest

from providers.base import BaseProvider, DatasetDescriptor
from shared.exceptions import DatasetNotFoundError
from shared.types import DatasetName, ProviderId


class _MinimalProvider(BaseProvider):
    """Minimal concrete provider used to test the base class contract."""

    @property
    def provider_id(self) -> ProviderId:
        return ProviderId("test_provider")

    @property
    def provider_name(self) -> str:
        return "Test Provider"

    @property
    def base_url(self) -> str:
        return "https://example.com/data"

    @property
    def license(self) -> str:
        return "MIT"

    def available_datasets(self) -> list[DatasetDescriptor]:
        return [
            DatasetDescriptor(
                name=DatasetName("results"),
                description="Test match results.",
                url_template="https://example.com/data/{season}.csv",
                license=self.license,
                default_params={"season": "2023"},
            )
        ]

    def build_url(self, dataset_name: DatasetName, **params: str) -> str:
        desc = self.get_descriptor(dataset_name)
        season = params.get("season", "2023")
        return desc.url_template.format(season=season)

    def parse(self, content: bytes, dataset_name: DatasetName) -> pd.DataFrame:
        import io

        return pd.read_csv(io.BytesIO(content))

    def normalise_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns={"HomeTeam": "home_team", "AwayTeam": "away_team"})


@pytest.fixture()
def provider() -> _MinimalProvider:
    return _MinimalProvider()


class TestBaseProviderContract:
    def test_provider_id_is_string_subtype(self, provider: _MinimalProvider) -> None:
        assert isinstance(provider.provider_id, str)

    def test_available_datasets_returns_list(self, provider: _MinimalProvider) -> None:
        datasets = provider.available_datasets()
        assert isinstance(datasets, list)
        assert len(datasets) > 0

    def test_get_descriptor_returns_correct_dataset(
        self, provider: _MinimalProvider
    ) -> None:
        desc = provider.get_descriptor(DatasetName("results"))
        assert desc.name == "results"

    def test_get_descriptor_raises_for_unknown_dataset(
        self, provider: _MinimalProvider
    ) -> None:
        with pytest.raises(DatasetNotFoundError) as exc_info:
            provider.get_descriptor(DatasetName("nonexistent"))
        assert "nonexistent" in str(exc_info.value)

    def test_build_url_uses_default_params(self, provider: _MinimalProvider) -> None:
        url = provider.build_url(DatasetName("results"))
        assert "2023" in url
        assert url.startswith("https://example.com")

    def test_build_url_uses_supplied_params(self, provider: _MinimalProvider) -> None:
        url = provider.build_url(DatasetName("results"), season="2024")
        assert "2024" in url

    def test_parse_returns_dataframe(self, provider: _MinimalProvider) -> None:
        csv = b"HomeTeam,AwayTeam\nArsenal,Chelsea\n"
        df = provider.parse(csv, DatasetName("results"))
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_normalise_columns_renames_correctly(
        self, provider: _MinimalProvider
    ) -> None:
        df = pd.DataFrame({"HomeTeam": ["Arsenal"], "AwayTeam": ["Chelsea"]})
        normalised = provider.normalise_columns(df)
        assert "home_team" in normalised.columns
        assert "away_team" in normalised.columns
        assert "HomeTeam" not in normalised.columns
