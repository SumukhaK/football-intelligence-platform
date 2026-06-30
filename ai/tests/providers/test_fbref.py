"""Tests for the FBref provider adapter."""

import pytest

from providers.fbref import FBrefProvider
from shared.exceptions import DatasetNotFoundError
from shared.types import DatasetName


@pytest.fixture()
def provider() -> FBrefProvider:
    return FBrefProvider()


class TestFBrefProvider:
    def test_provider_id(self, provider: FBrefProvider) -> None:
        assert provider.provider_id == "fbref"

    def test_provider_name(self, provider: FBrefProvider) -> None:
        assert "fbref" in provider.provider_name.lower()

    def test_has_scores_dataset(self, provider: FBrefProvider) -> None:
        names = [d.name for d in provider.available_datasets()]
        assert "scores_and_fixtures" in names

    def test_has_squad_stats_dataset(self, provider: FBrefProvider) -> None:
        names = [d.name for d in provider.available_datasets()]
        assert "squad_standard_stats" in names

    def test_build_url_default_params(self, provider: FBrefProvider) -> None:
        url = provider.build_url(DatasetName("scores_and_fixtures"))
        assert "fbref.com" in url
        assert "2023-2024" in url

    def test_build_url_custom_params(self, provider: FBrefProvider) -> None:
        url = provider.build_url(
            DatasetName("scores_and_fixtures"), comp_id="11", season="2022-2023"
        )
        assert "11" in url
        assert "2022-2023" in url

    def test_build_url_unknown_dataset(self, provider: FBrefProvider) -> None:
        with pytest.raises(DatasetNotFoundError):
            provider.build_url(DatasetName("nonexistent"))

    def test_parse_valid_csv(
        self, provider: FBrefProvider, fbref_raw_csv: bytes
    ) -> None:
        df = provider.parse(fbref_raw_csv, DatasetName("scores_and_fixtures"))
        assert len(df) == 1
        assert "Date" in df.columns

    def test_normalise_columns(
        self, provider: FBrefProvider, fbref_raw_csv: bytes
    ) -> None:
        df_raw = provider.parse(fbref_raw_csv, DatasetName("scores_and_fixtures"))
        df = provider.normalise_columns(df_raw)
        assert "date" in df.columns
        assert "home_team" in df.columns
        assert "away_team" in df.columns

    def test_normalise_drops_unmapped_columns(
        self, provider: FBrefProvider, fbref_raw_csv: bytes
    ) -> None:
        df_raw = provider.parse(fbref_raw_csv, DatasetName("scores_and_fixtures"))
        df = provider.normalise_columns(df_raw)
        assert "Home" not in df.columns
        assert "Away" not in df.columns
