"""Tests for the football-data.co.uk provider adapter."""

import pytest

from providers.football_data import FootballDataProvider
from schemas.match import DIVISION_TO_COMPETITION
from shared.exceptions import DatasetNotFoundError, IngestionError
from shared.types import DatasetName


@pytest.fixture()
def provider() -> FootballDataProvider:
    return FootballDataProvider()


class TestFootballDataProvider:
    def test_provider_id(self, provider: FootballDataProvider) -> None:
        assert provider.provider_id == "football_data"

    def test_provider_name(self, provider: FootballDataProvider) -> None:
        assert "football-data" in provider.provider_name.lower()

    def test_has_match_results_dataset(self, provider: FootballDataProvider) -> None:
        names = [d.name for d in provider.available_datasets()]
        assert "match_results" in names

    def test_build_url_default_params(self, provider: FootballDataProvider) -> None:
        url = provider.build_url(DatasetName("match_results"))
        assert "2324" in url
        assert "E0" in url
        assert url.startswith("https://")

    def test_build_url_custom_params(self, provider: FootballDataProvider) -> None:
        url = provider.build_url(
            DatasetName("match_results"), season="2223", division="E1"
        )
        assert "2223" in url
        assert "E1" in url

    @pytest.mark.parametrize("division", ["D1", "SP1", "I1", "F1"])
    def test_build_url_top_five_league_divisions(
        self, provider: FootballDataProvider, division: str
    ) -> None:
        url = provider.build_url(
            DatasetName("match_results"), season="0001", division=division
        )
        assert url.endswith(f"/0001/{division}.csv")

    def test_every_known_competition_division_is_downloadable(
        self, provider: FootballDataProvider
    ) -> None:
        for division in DIVISION_TO_COMPETITION:
            provider.build_url(DatasetName("match_results"), division=division)

    def test_build_url_invalid_division(self, provider: FootballDataProvider) -> None:
        with pytest.raises(DatasetNotFoundError):
            provider.build_url(DatasetName("match_results"), division="XX")

    def test_build_url_unknown_dataset(self, provider: FootballDataProvider) -> None:
        with pytest.raises(DatasetNotFoundError):
            provider.build_url(DatasetName("nonexistent"))

    def test_parse_valid_csv(
        self, provider: FootballDataProvider, football_data_raw_csv: bytes
    ) -> None:
        df = provider.parse(football_data_raw_csv, DatasetName("match_results"))
        assert len(df) == 2
        assert "HomeTeam" in df.columns
        assert "FTHG" in df.columns

    def test_parse_invalid_content_raises(self, provider: FootballDataProvider) -> None:
        # CSV parser is lenient; pass genuinely unparsable binary to trigger error
        with pytest.raises(IngestionError):
            # Force an error by patching read_csv in a subclass — instead, test
            # that completely empty bytes returns a valid (empty) df or raises
            df = provider.parse(b"", DatasetName("match_results"))
            # Empty CSV yields an empty DataFrame, which is acceptable
            assert len(df) == 0

    def test_normalise_columns_maps_known_columns(
        self, provider: FootballDataProvider, football_data_raw_csv: bytes
    ) -> None:
        df_raw = provider.parse(football_data_raw_csv, DatasetName("match_results"))
        df = provider.normalise_columns(df_raw)
        assert "home_team" in df.columns
        assert "away_team" in df.columns
        assert "home_goals_ft" in df.columns
        assert "away_goals_ft" in df.columns
        assert "result_ft" in df.columns

    def test_normalise_columns_drops_unmapped_columns(
        self, provider: FootballDataProvider, football_data_raw_csv: bytes
    ) -> None:
        df_raw = provider.parse(football_data_raw_csv, DatasetName("match_results"))
        df = provider.normalise_columns(df_raw)
        # Original provider-native names must not survive normalisation
        assert "HomeTeam" not in df.columns
        assert "FTHG" not in df.columns

    def test_parse_ignores_empty_trailing_fields(
        self, provider: FootballDataProvider
    ) -> None:
        # Some older season files pad rows with extra empty fields
        csv_padded = (
            b"Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
            b"E0,03/04/04,Newcastle,Everton,4,2,H\n"
            b"E0,03/04/04,Tottenham,Chelsea,0,1,A,,,,\n"
        )
        df = provider.parse(csv_padded, DatasetName("match_results"))
        assert len(df) == 2
        assert list(df.columns) == [
            "Div",
            "Date",
            "HomeTeam",
            "AwayTeam",
            "FTHG",
            "FTAG",
            "FTR",
        ]

    def test_parse_rejects_extra_non_empty_fields(
        self, provider: FootballDataProvider
    ) -> None:
        csv_ragged = (
            b"Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
            b"E0,03/04/04,Tottenham,Chelsea,0,1,A,,surprise\n"
        )
        with pytest.raises(IngestionError, match="line 2"):
            provider.parse(csv_ragged, DatasetName("match_results"))

    def test_parse_drops_empty_trailing_rows(
        self, provider: FootballDataProvider
    ) -> None:
        # football-data.co.uk files often end with a blank line
        csv_with_blank = (
            b"Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
            b"E0,01/08/2023,Arsenal,Chelsea,2,1,H\n"
            b"\n"
        )
        df = provider.parse(csv_with_blank, DatasetName("match_results"))
        assert len(df) == 1
