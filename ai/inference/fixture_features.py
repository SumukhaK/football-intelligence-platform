"""Pre-match features for a fixture, computed exactly as in training (ADR 008).

The fixture is appended as one row after every match played before its date
and run through the training feature pipeline. Every feature ignores the
current row's own result, so the values match what training saw for real
matches.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from feature_engineering.pipeline import FeaturePipeline, build_default_registry

# Newest in-progress snapshot first, then the completed-season history.
_DATASET_PATTERNS = ("match_results_live_v*.csv", "match_results_top5_v*.csv")


class UnknownTeamError(ValueError):
    """Raised when a team did not play in the competition's latest season."""

    def __init__(self, team: str, competition: str, season: str) -> None:
        """Record which team was not found and where it was looked up."""
        self.team = team
        self.competition = competition
        self.season = season
        super().__init__(f"'{team}' did not play in {competition} {season}")


@dataclass(frozen=True)
class Fixture:
    """A match to predict."""

    home_team: str
    away_team: str
    competition: str
    match_date: date


def season_for_date(day: date) -> str:
    """Return the season label a date falls in; seasons start on 1 July."""
    start = day.year if day.month >= 7 else day.year - 1
    return f"{start}/{(start + 1) % 100:02d}"


def find_latest_dataset(directory: Path) -> Path:
    """Return the newest live dataset, else the newest completed-season one.

    Raises:
        FileNotFoundError: If neither kind of dataset exists in ``directory``.
    """
    for pattern in _DATASET_PATTERNS:
        candidates = sorted(directory.glob(pattern))
        if candidates:
            return candidates[-1]
    raise FileNotFoundError(f"No match dataset in {directory}")


class FixtureFeatureBuilder:
    """Computes model features for fixtures from canonical match history."""

    def __init__(self, matches: pd.DataFrame) -> None:
        """Index canonical matches by competition."""
        registry = build_default_registry()
        self._pipeline = FeaturePipeline(registry)
        self._columns = [c for f in registry.get_ordered() for c in f.output_columns]
        frame = matches.assign(match_date=matches["match_date"].astype(str))
        self._by_competition = {
            str(comp): group.reset_index(drop=True)
            for comp, group in frame.groupby("competition")
        }
        self._cache: dict[Fixture, dict[str, float]] = {}

    @classmethod
    def from_directory(cls, directory: Path) -> FixtureFeatureBuilder:
        """Load the newest dataset in ``directory``."""
        return cls(pd.read_csv(find_latest_dataset(directory)))

    def teams(self, competition: str) -> tuple[str, list[str]]:
        """Return the latest season label and its teams, sorted by name.

        Raises:
            KeyError: If the competition is not in the data.
        """
        df = self._by_competition[competition]
        season = str(df["season"].max())
        latest = df[df["season"] == season]
        names = set(latest["home_team"]) | set(latest["away_team"])
        return season, sorted(str(n) for n in names)

    def build(self, fixture: Fixture) -> dict[str, float]:
        """Return every feature column for ``fixture``; missing values are NaN.

        Raises:
            KeyError: If the competition is not in the data.
            UnknownTeamError: If either team is not in the latest season.
        """
        if fixture in self._cache:
            return self._cache[fixture]
        season, known = self.teams(fixture.competition)
        for team in (fixture.home_team, fixture.away_team):
            if team not in known:
                raise UnknownTeamError(team, fixture.competition, season)
        features = self._compute(fixture)
        self._cache[fixture] = features
        return features

    def _compute(self, fixture: Fixture) -> dict[str, float]:
        """Run the feature pipeline over history plus the fixture row."""
        day = fixture.match_date.isoformat()
        history = self._by_competition[fixture.competition]
        history = history[history["match_date"] < day]
        row = {
            "match_date": day,
            "season": season_for_date(fixture.match_date),
            "competition": fixture.competition,
            "home_team": fixture.home_team,
            "away_team": fixture.away_team,
            # Placeholder outcome: no feature reads the current row's result.
            "full_time_home_goals": 0,
            "full_time_away_goals": 0,
            "result": "D",
        }
        matrix, _ = self._pipeline.compute(
            pd.concat([history, pd.DataFrame([row])], ignore_index=True)
        )
        last = matrix[matrix["match_date"] == day].iloc[-1]
        return {c: _as_float(last[c]) for c in self._columns}


def _as_float(value: object) -> float:
    """Convert a feature value to float, keeping missing values as NaN."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return float("nan")
    return float(value)  # type: ignore[arg-type]
