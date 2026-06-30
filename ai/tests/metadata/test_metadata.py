"""Tests for DatasetMetadata and MetadataBuilder."""

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from metadata.metadata import DatasetMetadata, MetadataBuilder
from shared.types import DatasetName, ProviderId


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2023-08-12", "2023-08-19"],
            "home_team": ["Arsenal", "Chelsea"],
            "away_team": ["Nottm Forest", "Liverpool"],
            "home_goals_ft": [2, 1],
            "away_goals_ft": [1, 1],
        }
    )


@pytest.fixture()
def raw_content() -> bytes:
    return b"date,home_team,away_team\n2023-08-12,Arsenal,Nottm Forest\n"


@pytest.fixture()
def fixed_ts() -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture()
def built_metadata(
    sample_df: pd.DataFrame, raw_content: bytes, fixed_ts: datetime
) -> DatasetMetadata:
    return MetadataBuilder.build(
        provider_id=ProviderId("football_data"),
        dataset_name=DatasetName("match_results"),
        source_url="https://example.com/data.csv",
        raw_content=raw_content,
        df=sample_df,
        license="Free for non-commercial use",
        downloaded_at=fixed_ts,
    )


class TestDatasetMetadataModel:
    def test_row_count_reflects_dataframe(
        self, built_metadata: DatasetMetadata, sample_df: pd.DataFrame
    ) -> None:
        assert built_metadata.row_count == len(sample_df)

    def test_column_count_reflects_dataframe(
        self, built_metadata: DatasetMetadata, sample_df: pd.DataFrame
    ) -> None:
        assert built_metadata.column_count == len(sample_df.columns)

    def test_columns_list_matches_dataframe(
        self, built_metadata: DatasetMetadata, sample_df: pd.DataFrame
    ) -> None:
        assert built_metadata.columns == list(sample_df.columns)

    def test_checksum_is_sha256_hex(self, built_metadata: DatasetMetadata) -> None:
        assert built_metadata.checksum_algorithm == "sha256"
        assert len(built_metadata.checksum) == 64  # SHA-256 hex digest length
        assert all(c in "0123456789abcdef" for c in built_metadata.checksum)

    def test_provider_id_recorded(self, built_metadata: DatasetMetadata) -> None:
        assert built_metadata.provider_id == "football_data"

    def test_dataset_name_recorded(self, built_metadata: DatasetMetadata) -> None:
        assert built_metadata.dataset_name == "match_results"

    def test_downloaded_at_is_utc(self, built_metadata: DatasetMetadata) -> None:
        assert built_metadata.downloaded_at.tzinfo is not None

    def test_dataset_version_derived_from_timestamp(
        self, built_metadata: DatasetMetadata, fixed_ts: datetime
    ) -> None:
        assert built_metadata.dataset_version == "20240101_120000"

    def test_is_immutable(self, built_metadata: DatasetMetadata) -> None:
        """Frozen Pydantic models raise ValidationError on mutation attempts."""
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            built_metadata.row_count = 999


class TestMetadataBuilderChecksum:
    def test_same_content_yields_same_checksum(
        self, raw_content: bytes, sample_df: pd.DataFrame, fixed_ts: datetime
    ) -> None:
        m1 = MetadataBuilder.build(
            provider_id=ProviderId("p"),
            dataset_name=DatasetName("d"),
            source_url="https://x.com",
            raw_content=raw_content,
            df=sample_df,
            license="MIT",
            downloaded_at=fixed_ts,
        )
        m2 = MetadataBuilder.build(
            provider_id=ProviderId("p"),
            dataset_name=DatasetName("d"),
            source_url="https://x.com",
            raw_content=raw_content,
            df=sample_df,
            license="MIT",
            downloaded_at=fixed_ts,
        )
        assert m1.checksum == m2.checksum

    def test_different_content_yields_different_checksum(
        self, sample_df: pd.DataFrame, fixed_ts: datetime
    ) -> None:
        m1 = MetadataBuilder.build(
            provider_id=ProviderId("p"),
            dataset_name=DatasetName("d"),
            source_url="https://x.com",
            raw_content=b"content_a",
            df=sample_df,
            license="MIT",
            downloaded_at=fixed_ts,
        )
        m2 = MetadataBuilder.build(
            provider_id=ProviderId("p"),
            dataset_name=DatasetName("d"),
            source_url="https://x.com",
            raw_content=b"content_b",
            df=sample_df,
            license="MIT",
            downloaded_at=fixed_ts,
        )
        assert m1.checksum != m2.checksum

    def test_verify_checksum_passes_for_original_content(
        self, built_metadata: DatasetMetadata, raw_content: bytes
    ) -> None:
        assert MetadataBuilder.verify_checksum(built_metadata, raw_content) is True

    def test_verify_checksum_fails_for_modified_content(
        self, built_metadata: DatasetMetadata
    ) -> None:
        assert (
            MetadataBuilder.verify_checksum(built_metadata, b"tampered content")
            is False
        )


class TestMetadataSerialisation:
    def test_roundtrip_json(self, built_metadata: DatasetMetadata) -> None:
        json_str = built_metadata.to_json()
        restored = DatasetMetadata.from_json(json_str)
        assert restored == built_metadata

    def test_save_and_load_from_file(
        self, built_metadata: DatasetMetadata, tmp_path: Path
    ) -> None:
        path = tmp_path / "metadata.json"
        MetadataBuilder.save(built_metadata, path)
        assert path.exists()
        loaded = MetadataBuilder.load(path)
        assert loaded == built_metadata

    def test_load_raises_on_invalid_json(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("not valid json", encoding="utf-8")
        with pytest.raises(ValueError):
            MetadataBuilder.load(path)
