"""Tests for scoring a season in progress — network-isolated."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from evaluation.in_season import build_season_features, match_predictions
from ingestion.in_progress import (
    IN_PROGRESS_DATASET,
    combine_with_history,
    fetch_in_progress,
)
from ingestion.storage import DatasetStorage
from providers.football_data import FootballDataProvider
from shared.exceptions import ValidationError

_URL = "https://www.football-data.co.uk/mmz4281/2627/E0.csv"
_HEADER = "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"
_AS_OF = date(2026, 9, 28)


class FakeTransport:
    """Serves one file and counts requests."""

    def __init__(self, content: bytes) -> None:
        self.content = content
        self.calls = 0

    def get(self, url: str, timeout: int) -> bytes:
        assert url == _URL
        self.calls += 1
        return self.content


def _csv(*rows: str) -> bytes:
    return (_HEADER + "".join(f"{r}\n" for r in rows)).encode("latin-1")


_PLAYED = _csv(
    "E0,15/08/26,Arsenal,Leeds,2,0,H,1.3,5.5,9.0",
    "E0,16/08/26,Chelsea,Everton,1,1,D,1.6,4.0,5.5",
    "E0,,Spurs,Fulham,,,,1.8,3.8,4.2",
)


def _fetch(storage: DatasetStorage, transport: FakeTransport) -> pd.DataFrame:
    return fetch_in_progress(
        FootballDataProvider(), storage, transport, ["E0"], "2627", _AS_OF
    )


def test_fetch_keeps_only_played_matches(tmp_storage: DatasetStorage) -> None:
    df = _fetch(tmp_storage, FakeTransport(_PLAYED))
    assert df["home_team"].tolist() == ["Arsenal", "Chelsea"]
    assert set(df["season"]) == {"2026/27"}


def test_fetch_reuses_the_same_day_snapshot(tmp_storage: DatasetStorage) -> None:
    first = FakeTransport(_PLAYED)
    _fetch(tmp_storage, first)
    second = FakeTransport(b"changed later in the day")
    _fetch(tmp_storage, second)
    assert (first.calls, second.calls) == (1, 0)
    assert tmp_storage.has_raw_partition(
        FootballDataProvider().provider_id, IN_PROGRESS_DATASET, "E0_2627_20260928"
    )


def test_fetch_rejects_inconsistent_results(tmp_storage: DatasetStorage) -> None:
    bad = _csv("E0,15/08/26,Arsenal,Leeds,2,0,A,1.3,5.5,9.0")
    with pytest.raises(ValidationError, match="result"):
        _fetch(tmp_storage, FakeTransport(bad))


def _canonical(day: str, season: str, home: str, away: str, res: str) -> dict:
    goals = {"H": (1, 0), "D": (0, 0), "A": (0, 1)}[res]
    return {
        "match_date": day,
        "season": season,
        "competition": "Premier League",
        "home_team": home,
        "away_team": away,
        "full_time_home_goals": goals[0],
        "full_time_away_goals": goals[1],
        "result": res,
    }


def test_build_season_features_uses_history_for_current_rows(tmp_path: Path) -> None:
    history = pd.DataFrame(
        [
            _canonical("2025-08-16", "2025/26", "A", "B", "H"),
            _canonical("2026-01-10", "2025/26", "B", "A", "A"),
        ]
    )
    current = pd.DataFrame(
        [
            _canonical("2026-08-15", "2026/27", "A", "B", "D"),
            _canonical("2026-08-22", "2026/27", "B", "A", "H"),
        ]
    )
    rows = build_season_features(history, current, tmp_path)
    assert len(rows) == 2
    assert rows["h2h_meetings"].tolist() == [2, 3]
    assert rows["home_league_points"].tolist() == [0, 1]
    assert rows["home_elo_before"].iloc[0] > 1500


def test_match_predictions_marks_correct_picks() -> None:
    rows = pd.DataFrame(
        {
            "match_date": ["2026-08-15", "2026-08-16"],
            "competition": ["Premier League", "Serie A"],
            "home_team": ["Arsenal", "Inter"],
            "away_team": ["Leeds", "Milan"],
            "result": ["H", "A"],
        }
    )
    probs = np.array([[0.1, 0.2, 0.7], [0.3, 0.4, 0.3]])
    table = match_predictions(rows, probs, ["A", "D", "H"])
    assert table["predicted"].tolist() == ["H", "D"]
    assert table["correct"].tolist() == [True, False]


def test_combine_with_history_appends_and_sorts() -> None:
    history = pd.DataFrame([_canonical("2026-01-10", "2025/26", "B", "A", "A")])
    current = pd.DataFrame([_canonical("2026-08-15", "2026/27", "A", "B", "D")])
    combined = combine_with_history(history, current)
    assert combined["season"].tolist() == ["2025/26", "2026/27"]


def test_combine_with_history_rejects_overlapping_season() -> None:
    rows = pd.DataFrame([_canonical("2026-08-15", "2026/27", "A", "B", "D")])
    with pytest.raises(ValidationError, match="2026/27"):
        combine_with_history(rows, rows)
