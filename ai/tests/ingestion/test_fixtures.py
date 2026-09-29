"""Tests for downloading upcoming fixtures (ADR 015) — network-isolated."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from config.team_names import OPENFOOTBALL_TEAM_NAMES
from ingestion.fixtures import (
    LEAGUES,
    refresh_fixtures,
    season_folder,
    upcoming_fixtures,
)
from shared.exceptions import ValidationError

TODAY = date(2026, 9, 29)


def _match(team1: str, team2: str, day: str, **extra: Any) -> dict[str, Any]:
    return {"round": "Matchday 6", "date": day, "team1": team1, "team2": team2, **extra}


def _schedule(*matches: dict[str, Any]) -> bytes:
    return json.dumps({"name": "League 2026/27", "matches": list(matches)}).encode()


PL_SCHEDULE = _schedule(
    _match("Arsenal FC", "Chelsea FC", "2026-09-20", score={"ft": [2, 1]}),
    _match("Liverpool FC", "Everton FC", "2026-09-27", score={}),
    _match("Arsenal FC", "Leeds United FC", "2026-10-10", time="12:30"),
    _match("Manchester City FC", "Fulham FC", "2026-10-11"),
)


class FakeTransport:
    """Serves one schedule per league file and counts requests."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def get(self, url: str, timeout: int) -> bytes:
        self.calls.append(url)
        if url.endswith("/2026-27/en.1.json"):
            return PL_SCHEDULE
        return _schedule()


@pytest.mark.parametrize(
    ("day", "folder"),
    [
        (date(2026, 9, 29), "2026-27"),
        (date(2027, 5, 1), "2026-27"),
        (date(2027, 7, 1), "2027-28"),
    ],
)
def test_season_folder(day: date, folder: str) -> None:
    assert season_folder(day) == folder


def test_only_unplayed_matches_from_today_are_kept() -> None:
    frame = upcoming_fixtures(PL_SCHEDULE, "Premier League", TODAY)
    assert list(frame["home_team"]) == ["Arsenal", "Man City"]


def test_team_names_match_the_results_data() -> None:
    frame = upcoming_fixtures(PL_SCHEDULE, "Premier League", TODAY)
    assert list(frame["away_team"]) == ["Leeds", "Fulham"]


def test_kickoff_carries_the_league_time_zone() -> None:
    frame = upcoming_fixtures(PL_SCHEDULE, "Premier League", TODAY)
    assert frame["kickoff"].iloc[0] == "2026-10-10T12:30:00+01:00"
    assert pd.isna(frame["kickoff"].iloc[1])


def test_an_unmapped_club_fails_loudly() -> None:
    schedule = _schedule(_match("Arsenal FC", "Unknown Town FC", "2026-10-10"))
    with pytest.raises(ValidationError, match="Unknown Town FC"):
        upcoming_fixtures(schedule, "Premier League", TODAY)


def test_a_repeated_pairing_fails() -> None:
    fixture = _match("Arsenal FC", "Chelsea FC", "2026-10-10")
    with pytest.raises(ValidationError, match="listed twice"):
        upcoming_fixtures(_schedule(fixture, fixture), "Premier League", TODAY)


def test_a_team_playing_itself_fails() -> None:
    schedule = _schedule(_match("Arsenal FC", "Arsenal FC", "2026-10-10"))
    with pytest.raises(ValidationError, match="cannot play itself"):
        upcoming_fixtures(schedule, "Premier League", TODAY)


def test_refresh_writes_a_dataset_and_keeps_raw_snapshots(tmp_path: Path) -> None:
    transport = FakeTransport()
    path = refresh_fixtures(tmp_path, TODAY, transport)
    assert path.parent == tmp_path / "processed" / "openfootball"
    assert len(pd.read_csv(path)) == 2
    raw = tmp_path / "raw" / "openfootball" / "fixtures"
    assert (raw / "en.1_2026-27_20260929.json").read_bytes() == PL_SCHEDULE
    assert len(transport.calls) == len(LEAGUES)


def test_a_second_refresh_on_the_same_day_reuses_the_download(tmp_path: Path) -> None:
    transport = FakeTransport()
    refresh_fixtures(tmp_path, TODAY, transport)
    refresh_fixtures(tmp_path, TODAY, transport)
    assert len(transport.calls) == len(LEAGUES)


def test_every_served_league_has_a_name_table() -> None:
    assert OPENFOOTBALL_TEAM_NAMES.keys() == LEAGUES.keys()


def test_name_table_covers_the_current_season() -> None:
    """Every 2026/27 club maps to a team in the latest results dataset."""
    results_dir = Path("../datasets/processed/football_data")
    results = sorted(results_dir.glob("match_results_live_v*.csv"))
    if not results:
        pytest.skip("No live results dataset available")
    frame = pd.read_csv(results[-1])
    frame = frame[frame["season"] == frame["season"].max()]
    for competition, names in OPENFOOTBALL_TEAM_NAMES.items():
        league = frame[frame["competition"] == competition]
        teams = set(league["home_team"]) | set(league["away_team"])
        assert set(names.values()) == teams, competition
