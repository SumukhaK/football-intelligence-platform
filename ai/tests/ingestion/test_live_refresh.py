"""Tests for rebuilding the live dataset — network-isolated."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from ingestion.live_refresh import (
    dataset_built_at,
    refresh_live_dataset,
    season_code_for,
)

_HEADER = "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"


class FakeTransport:
    """Serves one Premier League file for 2026/27 and counts requests."""

    def __init__(self) -> None:
        self.calls = 0

    def get(self, url: str, timeout: int) -> bytes:
        assert url.endswith("/2627/E0.csv")
        self.calls += 1
        return (_HEADER + "E0,15/08/26,Arsenal,Leeds,2,0,H,1.3,5.5,9.0\n").encode()


@pytest.mark.parametrize(
    ("day", "code"),
    [
        (date(2026, 9, 29), "2627"),
        (date(2027, 5, 20), "2627"),
        (date(2027, 7, 1), "2728"),
    ],
)
def test_season_code_for(day: date, code: str) -> None:
    assert season_code_for(day) == code


def test_refresh_appends_the_season_to_history(tmp_path: Path) -> None:
    processed = tmp_path / "processed" / "football_data"
    processed.mkdir(parents=True)
    history = pd.DataFrame(
        {
            "match_date": ["2026-05-20"],
            "season": ["2025/26"],
            "competition": ["Premier League"],
            "home_team": ["Arsenal"],
            "away_team": ["Chelsea"],
            "full_time_home_goals": [1],
            "full_time_away_goals": [1],
            "result": ["D"],
        }
    )
    history.to_csv(processed / "match_results_top5_v20260928_000000.csv", index=False)
    transport = FakeTransport()

    path = refresh_live_dataset(tmp_path, date(2026, 9, 29), ["E0"], transport)
    again = refresh_live_dataset(tmp_path, date(2026, 9, 29), ["E0"], transport)

    rows = pd.read_csv(path)
    assert rows["season"].tolist() == ["2025/26", "2026/27"]
    assert path.name.startswith("match_results_live_v")
    assert again.exists()
    assert transport.calls == 1  # the day's raw snapshot is reused


def test_refresh_needs_a_completed_history(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="backfill"):
        refresh_live_dataset(tmp_path, date(2026, 9, 29), ["E0"], FakeTransport())


def test_dataset_built_at_reads_the_version() -> None:
    built = dataset_built_at(Path("match_results_live_v20260928_172253.csv"))
    assert built == datetime(2026, 9, 28, 17, 22, 53, tzinfo=UTC)
    assert dataset_built_at(Path("notes.csv")) is None
