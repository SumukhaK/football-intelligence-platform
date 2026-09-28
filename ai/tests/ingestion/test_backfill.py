"""Tests for HistoryBackfill — network-isolated via a URL-keyed fake transport."""

from __future__ import annotations

from datetime import date, timedelta
from itertools import permutations

import pandas as pd
import pytest

from ingestion.backfill import COMBINED_DATASET, HistoryBackfill
from ingestion.storage import DatasetStorage
from providers.football_data import FootballDataProvider
from shared.exceptions import IngestionError, ValidationError
from shared.types import DatasetName

_HEADER = "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"


def _season_csv(division: str, teams: list[str], start: date) -> bytes:
    """Build a complete football-data style season CSV with home wins."""
    lines = [_HEADER]
    for i, (home, away) in enumerate(permutations(teams, 2)):
        day = (start + timedelta(days=i % 250)).strftime("%d/%m/%y")
        lines.append(f"{division},{day},{home},{away},2,1,H,1.9,3.4,4.0\n")
    return "".join(lines).encode("latin-1")


class FakeTransport:
    """Serves pre-registered bytes by URL and records every request."""

    def __init__(self, files: dict[str, bytes]) -> None:
        self._files = files
        self.requested: list[str] = []

    def get(self, url: str, timeout: int) -> bytes:
        self.requested.append(url)
        return self._files[url]


def _url(season: str, division: str) -> str:
    return f"https://www.football-data.co.uk/mmz4281/{season}/{division}.csv"


@pytest.fixture()
def files() -> dict[str, bytes]:
    d1 = [f"DE {i}" for i in range(18)]
    e0 = [f"EN {i}" for i in range(20)]
    return {
        _url("2223", "D1"): _season_csv("D1", d1, date(2022, 8, 5)),
        _url("2324", "D1"): _season_csv("D1", d1, date(2023, 8, 18)),
        _url("2324", "E0"): _season_csv("E0", e0, date(2023, 8, 11)),
    }


def _backfill(storage: DatasetStorage, transport: FakeTransport) -> HistoryBackfill:
    return HistoryBackfill(FootballDataProvider(), storage, transport=transport)


def test_plan_lists_every_division_season(tmp_storage: DatasetStorage) -> None:
    backfill = _backfill(tmp_storage, FakeTransport({}))
    plan = backfill.plan(["E0", "D1"], ["2223", "2324"])
    assert [(p.division, p.season_code) for p in plan] == [
        ("E0", "2223"),
        ("E0", "2324"),
        ("D1", "2223"),
        ("D1", "2324"),
    ]
    assert plan[0].url == _url("2223", "E0")
    assert not any(p.cached for p in plan)


def test_run_combines_seasons_into_one_processed_file(
    tmp_storage: DatasetStorage, files: dict[str, bytes]
) -> None:
    result = _backfill(tmp_storage, FakeTransport(files)).run(["D1"], ["2223", "2324"])
    df = pd.read_csv(result.processed_path)
    assert len(df) == 612
    assert result.row_count == 612
    assert set(df["season"]) == {"2022/23", "2023/24"}
    assert set(df["competition"]) == {"Bundesliga"}
    assert df["match_date"].is_monotonic_increasing
    assert COMBINED_DATASET in result.processed_path


def test_run_mixes_leagues(
    tmp_storage: DatasetStorage, files: dict[str, bytes]
) -> None:
    result = _backfill(tmp_storage, FakeTransport(files)).run(["E0", "D1"], ["2324"])
    df = pd.read_csv(result.processed_path)
    assert df.groupby("competition").size().to_dict() == {
        "Bundesliga": 306,
        "Premier League": 380,
    }


def test_second_run_reuses_stored_raw_files(
    tmp_storage: DatasetStorage, files: dict[str, bytes]
) -> None:
    first = FakeTransport(files)
    _backfill(tmp_storage, first).run(["D1"], ["2324"])
    second = FakeTransport(files)
    backfill = _backfill(tmp_storage, second)
    assert backfill.plan(["D1"], ["2324"])[0].cached
    backfill.run(["D1"], ["2324"])
    assert len(first.requested) == 1
    assert second.requested == []


def test_raw_files_are_stored_as_partitions(
    tmp_storage: DatasetStorage, files: dict[str, bytes]
) -> None:
    _backfill(tmp_storage, FakeTransport(files)).run(["D1"], ["2324"])
    raw = tmp_storage.load_raw_partition(
        FootballDataProvider().provider_id, DatasetName("match_results"), "D1_2324"
    )
    assert raw == files[_url("2324", "D1")]


def test_report_records_each_season(
    tmp_storage: DatasetStorage, files: dict[str, bytes]
) -> None:
    result = _backfill(tmp_storage, FakeTransport(files)).run(["E0"], ["2324"])
    [season] = result.seasons
    assert season.division == "E0"
    assert season.rows == 380
    assert season.failed_rows == 0
    assert season.url == _url("2324", "E0")
    assert len(season.checksum) == 64
    assert result.report_path.endswith("_report.json")


def test_integrity_failure_raises_and_writes_no_dataset(
    tmp_storage: DatasetStorage, files: dict[str, bytes]
) -> None:
    truncated = files[_url("2324", "E0")].decode("latin-1").splitlines(keepends=True)
    files[_url("2324", "E0")] = "".join(truncated[:-1]).encode("latin-1")
    with pytest.raises(ValidationError, match="379 matches"):
        _backfill(tmp_storage, FakeTransport(files)).run(["E0"], ["2324"])
    processed = tmp_storage._paths.processed / "football_data"
    assert not list(processed.glob(f"{COMBINED_DATASET}_v*.csv"))
    assert list(processed.glob(f"{COMBINED_DATASET}_v*_report.json"))


def test_too_many_unparseable_rows_raises(
    tmp_storage: DatasetStorage, files: dict[str, bytes]
) -> None:
    text = files[_url("2324", "E0")].decode("latin-1").splitlines(keepends=True)
    text[1:3] = [line.replace(",2,1,H,", ",x,1,H,") for line in text[1:3]]
    files[_url("2324", "E0")] = "".join(text).encode("latin-1")
    with pytest.raises(IngestionError, match="E0 2324"):
        _backfill(tmp_storage, FakeTransport(files)).run(["E0"], ["2324"])
