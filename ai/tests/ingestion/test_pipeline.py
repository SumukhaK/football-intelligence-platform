"""Tests for IngestionPipeline — all network-isolated via FakeTransport."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ingestion.pipeline import IngestionPipeline, PipelineResult
from ingestion.storage import DatasetStorage
from providers.football_data import FootballDataProvider
from shared.exceptions import IngestionError, ValidationError
from shared.types import DatasetName

# ---------------------------------------------------------------------------
# FakeTransport
# ---------------------------------------------------------------------------


class FakeTransport:
    """Returns pre-configured bytes without touching the network."""

    def __init__(self, content: bytes) -> None:
        self._content = content

    def get(self, url: str, timeout: int) -> bytes:
        return self._content


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_FULL_CSV = (
    "Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,"
    "HTHG,HTAG,HTR,Referee,HS,AS,HST,AST,HF,AF,HC,AC,"
    "HY,AY,HR,AR,B365H,B365D,B365A\n"
    "E0,12/08/2023,12:30,Arsenal,Nottm Forest,2,1,H,"
    "1,0,H,M. Oliver,12,8,5,3,10,12,6,4,"
    "1,2,0,0,1.95,3.50,4.20\n"
    "E0,19/08/2023,15:00,Chelsea,Liverpool,1,1,D,"
    "0,1,A,A. Taylor,10,9,4,4,8,9,5,5,"
    "2,1,0,0,2.10,3.40,3.60\n"
)

_MINIMAL_CSV = (
    "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n" "E0,12/08/2023,Arsenal,Forest,2,1,H\n"
)

_EMPTY_CSV = "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"


@pytest.fixture()
def provider() -> FootballDataProvider:
    return FootballDataProvider()


@pytest.fixture()
def pipeline(
    provider: FootballDataProvider, tmp_storage: DatasetStorage
) -> IngestionPipeline:
    return IngestionPipeline(
        provider=provider,
        storage=tmp_storage,
        transport=FakeTransport(_FULL_CSV.encode("latin-1")),
    )


@pytest.fixture()
def dataset_name_fixture() -> DatasetName:
    return DatasetName("match_results")


# ---------------------------------------------------------------------------
# Successful runs
# ---------------------------------------------------------------------------


def test_pipeline_run_returns_result(
    pipeline: IngestionPipeline,
    dataset_name_fixture: DatasetName,
) -> None:
    result = pipeline.run(dataset_name_fixture, season_code="2324", division="E0")
    assert isinstance(result, PipelineResult)
    assert result.row_count == 2
    assert result.failed_rows == 0
    assert result.season == "2023/24"
    assert result.competition == "Premier League"
    assert result.division == "E0"


def test_pipeline_run_creates_raw_file(
    pipeline: IngestionPipeline,
    dataset_name_fixture: DatasetName,
) -> None:
    result = pipeline.run(dataset_name_fixture, season_code="2324", division="E0")
    assert Path(result.raw_path).exists()
    raw_bytes = Path(result.raw_path).read_bytes()
    assert b"Arsenal" in raw_bytes


def test_pipeline_run_creates_processed_file(
    pipeline: IngestionPipeline,
    dataset_name_fixture: DatasetName,
) -> None:
    result = pipeline.run(dataset_name_fixture, season_code="2324", division="E0")
    processed = pd.read_csv(result.processed_path)
    assert "match_date" in processed.columns
    assert "competition" in processed.columns
    assert len(processed) == 2


def test_pipeline_run_creates_metadata_file(
    pipeline: IngestionPipeline,
    dataset_name_fixture: DatasetName,
) -> None:
    result = pipeline.run(dataset_name_fixture, season_code="2324", division="E0")
    assert Path(result.metadata_path).exists()
    # checksum is stored as raw hex (64 chars for sha256)
    assert len(result.checksum) == 64


def test_pipeline_run_processed_contains_canonical_fields(
    pipeline: IngestionPipeline,
    dataset_name_fixture: DatasetName,
) -> None:
    result = pipeline.run(dataset_name_fixture, season_code="2324", division="E0")
    df = pd.read_csv(result.processed_path)
    expected = {
        "match_date",
        "season",
        "competition",
        "home_team",
        "away_team",
        "full_time_home_goals",
        "full_time_away_goals",
        "result",
    }
    assert expected.issubset(set(df.columns))


def test_pipeline_run_minimal_csv_no_optional_stats(
    provider: FootballDataProvider,
    tmp_storage: DatasetStorage,
    dataset_name_fixture: DatasetName,
) -> None:
    pipeline = IngestionPipeline(
        provider=provider,
        storage=tmp_storage,
        transport=FakeTransport(_MINIMAL_CSV.encode("latin-1")),
    )
    result = pipeline.run(dataset_name_fixture, season_code="2324", division="E0")
    assert result.row_count == 1
    df = pd.read_csv(result.processed_path)
    assert df["home_shots"].isna().all()


# ---------------------------------------------------------------------------
# Validation failures
# ---------------------------------------------------------------------------


def test_pipeline_raises_on_empty_dataset(
    provider: FootballDataProvider,
    tmp_storage: DatasetStorage,
    dataset_name_fixture: DatasetName,
) -> None:
    pipeline = IngestionPipeline(
        provider=provider,
        storage=tmp_storage,
        transport=FakeTransport(_EMPTY_CSV.encode("latin-1")),
    )
    with pytest.raises(ValidationError):
        pipeline.run(dataset_name_fixture, season_code="2324", division="E0")


def test_pipeline_raises_on_missing_required_column(
    provider: FootballDataProvider,
    tmp_storage: DatasetStorage,
    dataset_name_fixture: DatasetName,
) -> None:
    # CSV missing FTHG / FTAG columns
    bad_csv = (
        "Div,Date,HomeTeam,AwayTeam,FTR\n" "E0,12/08/2023,Arsenal,Forest,H\n"
    ).encode("latin-1")
    pipeline = IngestionPipeline(
        provider=provider,
        storage=tmp_storage,
        transport=FakeTransport(bad_csv),
    )
    with pytest.raises(ValidationError):
        pipeline.run(dataset_name_fixture, season_code="2324", division="E0")


def test_pipeline_raises_when_all_rows_fail_normalisation(
    provider: FootballDataProvider,
    tmp_storage: DatasetStorage,
    dataset_name_fixture: DatasetName,
) -> None:
    # Valid CSV structure but date is unparseable after normalise_columns
    bad_date_csv = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n" "E0,INVALID,Arsenal,Forest,2,1,H\n"
    ).encode("latin-1")
    pipeline = IngestionPipeline(
        provider=provider,
        storage=tmp_storage,
        transport=FakeTransport(bad_date_csv),
    )
    with pytest.raises(IngestionError):
        pipeline.run(dataset_name_fixture, season_code="2324", division="E0")


# ---------------------------------------------------------------------------
# Extra rules
# ---------------------------------------------------------------------------


def test_pipeline_accepts_extra_validation_rules(
    pipeline: IngestionPipeline,
    dataset_name_fixture: DatasetName,
) -> None:
    from validation.dataset_validator import RowCountRule

    result = pipeline.run(
        dataset_name_fixture,
        season_code="2324",
        division="E0",
        extra_rules=[RowCountRule(min_rows=2)],
    )
    assert result.row_count == 2


def test_pipeline_extra_rules_can_fail(
    pipeline: IngestionPipeline,
    dataset_name_fixture: DatasetName,
) -> None:
    from validation.dataset_validator import RowCountRule

    with pytest.raises(ValidationError):
        pipeline.run(
            dataset_name_fixture,
            season_code="2324",
            division="E0",
            extra_rules=[RowCountRule(min_rows=999)],
        )


# ---------------------------------------------------------------------------
# Integration test (network — skipped in CI)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_pipeline_downloads_real_epl_2324(tmp_path: Path) -> None:
    """Downloads the real 2023/24 EPL CSV. Requires network access."""
    from config.paths import DataPaths
    from ingestion.pipeline import IngestionPipeline
    from ingestion.storage import DatasetStorage
    from providers.football_data import FootballDataProvider

    paths = DataPaths(base_dir=tmp_path / "datasets")
    paths.ensure_all()
    storage = DatasetStorage(paths)
    provider = FootballDataProvider()
    pipeline = IngestionPipeline(provider=provider, storage=storage)
    result = pipeline.run(
        DatasetName("match_results"), season_code="2324", division="E0"
    )
    assert result.row_count > 300
    assert result.failed_rows == 0
    assert Path(result.processed_path).exists()
