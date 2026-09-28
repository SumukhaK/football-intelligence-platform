"""Tests for DatasetStorage."""

import pandas as pd
import pytest

from ingestion.storage import DatasetStorage
from shared.exceptions import StorageError
from shared.types import DatasetName, DatasetVersion, ProviderId


@pytest.fixture()
def provider_id() -> ProviderId:
    return ProviderId("football_data")


@pytest.fixture()
def dataset_name() -> DatasetName:
    return DatasetName("match_results")


@pytest.fixture()
def version() -> DatasetVersion:
    return DatasetVersion("20240101_120000")


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2023-08-12"],
            "home_team": ["Arsenal"],
            "away_team": ["Nottm Forest"],
        }
    )


@pytest.fixture()
def raw_content() -> bytes:
    return b"date,home_team,away_team\n2023-08-12,Arsenal,Nottm Forest\n"


class TestDatasetStorageRaw:
    def test_save_and_load_raw(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        version: DatasetVersion,
        raw_content: bytes,
    ) -> None:
        tmp_storage.save_raw(raw_content, provider_id, dataset_name, version)
        loaded = tmp_storage.load_raw(provider_id, dataset_name, version)
        assert loaded == raw_content

    def test_load_raw_raises_when_missing(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        version: DatasetVersion,
    ) -> None:
        with pytest.raises(StorageError):
            tmp_storage.load_raw(provider_id, dataset_name, version)

    def test_save_raw_creates_parent_directories(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        version: DatasetVersion,
        raw_content: bytes,
    ) -> None:
        path = tmp_storage.save_raw(raw_content, provider_id, dataset_name, version)
        assert path.exists()
        assert path.is_file()


class TestDatasetStorageDataFrame:
    def test_save_and_load_dataframe(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        version: DatasetVersion,
        sample_df: pd.DataFrame,
    ) -> None:
        tmp_storage.save_dataframe(sample_df, provider_id, dataset_name, version)
        loaded = tmp_storage.load_dataframe(provider_id, dataset_name, version)
        assert list(loaded.columns) == list(sample_df.columns)
        assert len(loaded) == len(sample_df)

    def test_load_dataframe_raises_when_missing(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        version: DatasetVersion,
    ) -> None:
        with pytest.raises(StorageError):
            tmp_storage.load_dataframe(provider_id, dataset_name, version)


class TestDatasetStorageVersionListing:
    def test_list_versions_returns_empty_when_none_stored(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
    ) -> None:
        versions = tmp_storage.list_versions(provider_id, dataset_name)
        assert versions == []

    def test_list_versions_returns_stored_versions(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        raw_content: bytes,
    ) -> None:
        v1 = DatasetVersion("20240101_120000")
        v2 = DatasetVersion("20240102_120000")
        tmp_storage.save_raw(raw_content, provider_id, dataset_name, v1)
        tmp_storage.save_raw(raw_content, provider_id, dataset_name, v2)
        versions = tmp_storage.list_versions(provider_id, dataset_name)
        assert v1 in versions
        assert v2 in versions
        assert versions == sorted(versions)


class TestDatasetStorageRawPartitions:
    def test_save_and_load_raw_partition(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        raw_content: bytes,
    ) -> None:
        path = tmp_storage.save_raw_partition(
            raw_content, provider_id, dataset_name, "E0_2324"
        )
        assert path.name == "E0_2324.csv"
        assert path.parent.name == dataset_name
        assert (
            tmp_storage.load_raw_partition(provider_id, dataset_name, "E0_2324")
            == raw_content
        )

    def test_has_raw_partition(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        raw_content: bytes,
    ) -> None:
        assert not tmp_storage.has_raw_partition(provider_id, dataset_name, "D1_0001")
        tmp_storage.save_raw_partition(
            raw_content, provider_id, dataset_name, "D1_0001"
        )
        assert tmp_storage.has_raw_partition(provider_id, dataset_name, "D1_0001")

    def test_saving_identical_partition_twice_is_a_no_op(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        raw_content: bytes,
    ) -> None:
        first = tmp_storage.save_raw_partition(
            raw_content, provider_id, dataset_name, "E0_2324"
        )
        second = tmp_storage.save_raw_partition(
            raw_content, provider_id, dataset_name, "E0_2324"
        )
        assert first == second

    def test_overwriting_partition_with_different_content_raises(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        raw_content: bytes,
    ) -> None:
        tmp_storage.save_raw_partition(
            raw_content, provider_id, dataset_name, "E0_2324"
        )
        with pytest.raises(StorageError, match="immutable"):
            tmp_storage.save_raw_partition(
                raw_content + b"extra\n", provider_id, dataset_name, "E0_2324"
            )

    def test_load_missing_partition_raises(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
    ) -> None:
        with pytest.raises(StorageError):
            tmp_storage.load_raw_partition(provider_id, dataset_name, "E0_9999")

    def test_partitions_do_not_appear_in_version_listing(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        dataset_name: DatasetName,
        raw_content: bytes,
    ) -> None:
        tmp_storage.save_raw_partition(
            raw_content, provider_id, dataset_name, "E0_2324"
        )
        assert tmp_storage.list_versions(provider_id, dataset_name) == []


class TestDatasetStorageReport:
    def test_save_report_writes_json_next_to_processed_file(
        self,
        tmp_storage: DatasetStorage,
        provider_id: ProviderId,
        version: DatasetVersion,
    ) -> None:
        name = DatasetName("match_results_top5")
        path = tmp_storage.save_report({"rows": 3}, provider_id, name, version)
        assert path.name == f"match_results_top5_v{version}_report.json"
        assert path.parent.name == provider_id
        assert '"rows": 3' in path.read_text(encoding="utf-8")
