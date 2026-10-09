"""Shared pytest fixtures for the football AI workspace test suite."""

import json
import logging
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from config.paths import DataPaths
from ingestion.storage import DatasetStorage
from shared.types import DatasetName, DatasetVersion, ProviderId, SchemaVersion

# ---------------------------------------------------------------------------
# Network isolation
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def no_live_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep app startup in tests from downloading data (ADR 013).

    Tests that run the lifespan would otherwise start the daily refresh and,
    when the real dataset is stale, download today's results into it.
    """
    import backend.app.main as main

    monkeypatch.setattr(main, "_start_live_refresh", lambda app: None)


# ---------------------------------------------------------------------------
# Telemetry events
# ---------------------------------------------------------------------------

EventRecords = list[logging.LogRecord]


class _EventCollector(logging.Handler):
    """Keeps every log record that carries a contract event."""

    def __init__(self) -> None:
        super().__init__()
        self.records: EventRecords = []

    def emit(self, record: logging.LogRecord) -> None:
        if getattr(record, "event", None):
            self.records.append(record)


@pytest.fixture(scope="session")
def session_events() -> Iterator[EventRecords]:
    """Every event emitted during the test session, for the conformance test."""
    collector = _EventCollector()
    root = logging.getLogger()
    root.addHandler(collector)
    yield collector.records
    root.removeHandler(collector)


@pytest.fixture(autouse=True)
def _collect_session_events(session_events: EventRecords) -> None:
    """Install the session collector before every test."""


@pytest.fixture()
def events(
    caplog: pytest.LogCaptureFixture,
) -> Callable[[str], list[tuple[str, dict[str, Any]]]]:
    """Return a lookup of (severity, attributes) for each emitted ``event``."""
    caplog.set_level(logging.DEBUG)

    def by_name(name: str) -> list[tuple[str, dict[str, Any]]]:
        return [
            (record.levelname, record.__dict__["attributes"])
            for record in caplog.records
            if getattr(record, "event", None) == name
        ]

    return by_name


# ---------------------------------------------------------------------------
# DataPaths / storage fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_data_paths(tmp_path: Path) -> DataPaths:
    """A DataPaths instance rooted in pytest's temporary directory."""
    paths = DataPaths(base_dir=tmp_path / "datasets")
    paths.ensure_all()
    return paths


@pytest.fixture()
def tmp_storage(tmp_data_paths: DataPaths) -> DatasetStorage:
    """A DatasetStorage backed by the temporary DataPaths fixture."""
    return DatasetStorage(tmp_data_paths)


# ---------------------------------------------------------------------------
# DataFrames
# ---------------------------------------------------------------------------


@pytest.fixture()
def football_data_raw_csv() -> bytes:
    """Minimal CSV bytes in football-data.co.uk format."""
    content = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HS,AS,HST,AST\n"
        "E0,01/08/2023,Arsenal,Nottm Forest,2,1,H,12,8,5,3\n"
        "E0,02/08/2023,Chelsea,Liverpool,1,1,D,10,9,4,4\n"
    )
    return content.encode("latin-1")


@pytest.fixture()
def fbref_raw_csv() -> bytes:
    """Minimal CSV bytes in FBref scores-and-fixtures format."""
    content = (
        "Wk,Day,Date,Time,Home,xG,Score,xG.1,Away,Attendance,Venue,Referee\n"
        "1,Sat,2023-08-12,12:30,Arsenal,1.8,2-1,0.6,"
        "Nottm Forest,60346,Emirates,M.Oliver\n"
    )
    return content.encode("utf-8")


@pytest.fixture()
def understat_raw_json() -> bytes:
    """Minimal JSON bytes in Understat match-list format."""
    records = [
        {
            "id": "17732",
            "isResult": True,
            "datetime": "2023-08-12 12:30:00",
            "season": "2023",
            "h": {
                "title": "Arsenal",
                "goals": "2",
                "xg": "1.8",
                "w": "0.65",
                "d": "0.22",
                "l": "0.13",
            },
            "a": {
                "title": "Nottm Forest",
                "goals": "1",
                "xg": "0.6",
                "w": "0.13",
                "d": "0.22",
                "l": "0.65",
            },
        }
    ]
    return json.dumps(records).encode("utf-8")


@pytest.fixture()
def normalised_match_df() -> pd.DataFrame:
    """A normalised DataFrame matching platform-standard column names."""
    return pd.DataFrame(
        {
            "date": ["01/08/2023", "02/08/2023"],
            "home_team": ["Arsenal", "Chelsea"],
            "away_team": ["Nottm Forest", "Liverpool"],
            "home_goals_ft": [2, 1],
            "away_goals_ft": [1, 1],
            "result_ft": ["H", "D"],
        }
    )


# ---------------------------------------------------------------------------
# Shared value fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def provider_id() -> ProviderId:
    return ProviderId("football_data")


@pytest.fixture()
def dataset_name() -> DatasetName:
    return DatasetName("match_results")


@pytest.fixture()
def dataset_version() -> DatasetVersion:
    return DatasetVersion("20240101_120000")


@pytest.fixture()
def schema_version() -> SchemaVersion:
    return SchemaVersion("1.0.0")


@pytest.fixture()
def fixed_timestamp() -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
