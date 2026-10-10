"""Upcoming fixtures for the five served leagues, from openfootball (ADR 015).

Each league's season schedule is stored once per day as an immutable raw
partition. Matches not yet played are renamed to football-data.co.uk team
names, validated and written as ``processed/openfootball/fixtures_v<ts>.csv``.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Final
from zoneinfo import ZoneInfo

import pandas as pd
from pydantic import ValidationError as SchemaError

from config.paths import DataPaths
from config.team_names import OPENFOOTBALL_TEAM_NAMES
from ingestion.downloader import HttpTransport, HttpxTransport
from ingestion.storage import DatasetStorage
from schemas.fixture import FIXTURE_COLUMNS, ProcessedFixture
from shared.exceptions import ValidationError
from shared.types import DatasetName, DatasetVersion, ProviderId

OPENFOOTBALL = ProviderId("openfootball")
FIXTURES_DATASET = DatasetName("fixtures")
_URL: Final = (
    "https://raw.githubusercontent.com/openfootball/football.json/master/"
    "{season}/{code}.json"
)

# League → (openfootball file code, time zone its kick-off times are in).
LEAGUES: Final[dict[str, tuple[str, str]]] = {
    "Premier League": ("en.1", "Europe/London"),
    "Bundesliga": ("de.1", "Europe/Berlin"),
    "La Liga": ("es.1", "Europe/Madrid"),
    "Serie A": ("it.1", "Europe/Rome"),
    "Ligue 1": ("fr.1", "Europe/Paris"),
}


def season_folder(day: date) -> str:
    """openfootball's season folder for a date; seasons start on 1 July.

    Example: 29 September 2026 → ``"2026-27"``.
    """
    start = day.year if day.month >= 7 else day.year - 1
    return f"{start}-{(start + 1) % 100:02d}"


def refresh_fixtures(
    base_dir: Path, as_of: date, transport: HttpTransport | None = None
) -> Path:
    """Download every league's schedule and write a new fixtures dataset.

    Raises:
        IngestionError: If a download fails.
        ValidationError: If a league has an unmapped team or a bad fixture.
    """
    storage = DatasetStorage(DataPaths(base_dir=base_dir))
    frames = [
        upcoming_fixtures(
            _load_or_download(
                storage, transport or HttpxTransport("openfootball"), code, as_of
            ),
            competition,
            as_of,
        )
        for competition, (code, _zone) in LEAGUES.items()
    ]
    version = DatasetVersion(datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S"))
    return storage.save_dataframe(
        pd.concat(frames, ignore_index=True), OPENFOOTBALL, FIXTURES_DATASET, version
    )


def _load_or_download(
    storage: DatasetStorage, transport: HttpTransport, code: str, as_of: date
) -> bytes:
    """Return the stored schedule for ``as_of``, downloading it if missing."""
    season = season_folder(as_of)
    partition = f"{code}_{season}_{as_of:%Y%m%d}"
    if storage.has_raw_partition(OPENFOOTBALL, FIXTURES_DATASET, partition, ".json"):
        return storage.load_raw_partition(
            OPENFOOTBALL, FIXTURES_DATASET, partition, ".json"
        )
    content = transport.get(_URL.format(season=season, code=code), timeout=30)
    storage.save_raw_partition(
        content, OPENFOOTBALL, FIXTURES_DATASET, partition, ".json"
    )
    return content


def upcoming_fixtures(content: bytes, competition: str, as_of: date) -> pd.DataFrame:
    """Validated fixtures on or after ``as_of`` from one league's schedule.

    Raises:
        ValidationError: On unmapped teams, invalid rows or repeated pairings.
    """
    matches: list[dict[str, Any]] = json.loads(content)["matches"]
    _check_team_names(matches, competition)
    _check_unique_pairings(matches, competition)
    zone = ZoneInfo(LEAGUES[competition][1])
    rows = [
        _row(match, competition, zone)
        for match in matches
        if "ft" not in match.get("score", {})
        and date.fromisoformat(match["date"]) >= as_of
    ]
    return pd.DataFrame(rows, columns=FIXTURE_COLUMNS)


def _check_team_names(matches: list[dict[str, Any]], competition: str) -> None:
    """Fail loudly when a club is missing from the name table."""
    names = OPENFOOTBALL_TEAM_NAMES[competition]
    unknown = sorted(
        {m[side] for m in matches for side in ("team1", "team2")} - names.keys()
    )
    if unknown:
        raise ValidationError(
            f"{competition} fixtures",
            f"Add these clubs to config/team_names.py: {unknown}",
        )


def _check_unique_pairings(matches: list[dict[str, Any]], competition: str) -> None:
    """Each home/away pairing is played once a season."""
    pairs = [(m["team1"], m["team2"]) for m in matches]
    repeated = sorted({p for p in pairs if pairs.count(p) > 1})
    if repeated:
        raise ValidationError(
            f"{competition} fixtures", f"Pairings listed twice: {repeated}"
        )


def _row(match: dict[str, Any], competition: str, zone: ZoneInfo) -> dict[str, Any]:
    """One schema-checked fixture row with football-data team names."""
    names = OPENFOOTBALL_TEAM_NAMES[competition]
    kickoff = None
    if match.get("time"):
        local = datetime.fromisoformat(f"{match['date']}T{match['time']}")
        kickoff = local.replace(tzinfo=zone)
    try:
        fixture = ProcessedFixture(
            competition=competition,
            match_date=date.fromisoformat(match["date"]),
            kickoff=kickoff,
            home_team=names[match["team1"]],
            away_team=names[match["team2"]],
            round=match["round"],
        )
    except SchemaError as exc:
        raise ValidationError(f"{competition} fixtures", str(exc)) from exc
    row = fixture.model_dump()
    row["kickoff"] = kickoff.isoformat() if kickoff else None
    return row
