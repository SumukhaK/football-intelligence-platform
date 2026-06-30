"""Tests for the Understat provider adapter."""

import json

import pytest

from providers.understat import UnderstatProvider
from shared.exceptions import DatasetNotFoundError, IngestionError
from shared.types import DatasetName


@pytest.fixture()
def provider() -> UnderstatProvider:
    return UnderstatProvider()


class TestUnderstatProvider:
    def test_provider_id(self, provider: UnderstatProvider) -> None:
        assert provider.provider_id == "understat"

    def test_provider_name(self, provider: UnderstatProvider) -> None:
        assert "understat" in provider.provider_name.lower()

    def test_has_match_results_dataset(self, provider: UnderstatProvider) -> None:
        names = [d.name for d in provider.available_datasets()]
        assert "match_results" in names

    def test_build_url_default_params(self, provider: UnderstatProvider) -> None:
        url = provider.build_url(DatasetName("match_results"))
        assert "understat.com" in url
        assert "EPL" in url
        assert "2023" in url

    def test_build_url_custom_params(self, provider: UnderstatProvider) -> None:
        url = provider.build_url(
            DatasetName("match_results"), league="La_liga", season="2022"
        )
        assert "La_liga" in url
        assert "2022" in url

    def test_build_url_unknown_dataset(self, provider: UnderstatProvider) -> None:
        with pytest.raises(DatasetNotFoundError):
            provider.build_url(DatasetName("nonexistent"))

    def test_parse_valid_json(
        self, provider: UnderstatProvider, understat_raw_json: bytes
    ) -> None:
        df = provider.parse(understat_raw_json, DatasetName("match_results"))
        assert len(df) == 1
        assert "h_title" in df.columns or "home_team" in df.columns

    def test_parse_invalid_json_raises(self, provider: UnderstatProvider) -> None:
        with pytest.raises(IngestionError):
            provider.parse(b"not json", DatasetName("match_results"))

    def test_parse_non_list_json_raises(self, provider: UnderstatProvider) -> None:
        with pytest.raises(IngestionError):
            provider.parse(
                json.dumps({"key": "value"}).encode(), DatasetName("match_results")
            )

    def test_parse_flattens_nested_h_and_a(
        self, provider: UnderstatProvider, understat_raw_json: bytes
    ) -> None:
        df = provider.parse(understat_raw_json, DatasetName("match_results"))
        # Nested "h" dict should be flattened to h_* columns
        assert any(col.startswith("h_") for col in df.columns)
        assert any(col.startswith("a_") for col in df.columns)
        # Original "h" and "a" keys should not appear as columns
        assert "h" not in df.columns
        assert "a" not in df.columns

    def test_normalise_columns(
        self, provider: UnderstatProvider, understat_raw_json: bytes
    ) -> None:
        df_raw = provider.parse(understat_raw_json, DatasetName("match_results"))
        df = provider.normalise_columns(df_raw)
        assert "date" in df.columns
        assert "home_team" in df.columns
        assert "away_team" in df.columns
        assert "home_goals_ft" in df.columns
        assert "away_goals_ft" in df.columns
