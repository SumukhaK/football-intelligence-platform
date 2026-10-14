"""Upcoming fixtures per league, read from the processed fixtures dataset."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from backend.app.schemas.fixtures import Fixture, FixturesResponse
from ingestion.live_refresh import dataset_built_at


def find_latest_fixtures(directory: Path) -> Path:
    """The newest ``fixtures_v*.csv`` in ``directory``.

    Raises:
        FileNotFoundError: If there is none.
    """
    files = sorted(directory.glob("fixtures_v*.csv"))
    if not files:
        raise FileNotFoundError(f"No fixtures dataset in {directory}")
    return files[-1]


class FixturesService:
    """Answers "what's coming up in this league" from one fixtures dataset."""

    def __init__(
        self,
        frame: pd.DataFrame,
        today: Callable[[], date],
        updated_at: datetime | None = None,
    ) -> None:
        """Initialise with fixture rows, a clock and the download time."""
        # Matches without a confirmed time go after the day's timed matches.
        self._frame = (
            frame.fillna("")
            .assign(_time_unknown=lambda f: f["kickoff"] == "")
            .sort_values(
                ["match_date", "_time_unknown", "kickoff", "home_team"], kind="stable"
            )
        )
        self._today = today
        self.updated_at = updated_at

    @classmethod
    def from_directory(
        cls, directory: Path, today: Callable[[], date]
    ) -> FixturesService:
        """Load the newest fixtures dataset in ``directory``.

        Raises:
            FileNotFoundError: If there is none.
        """
        path = find_latest_fixtures(directory)
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        return cls(frame, today, dataset_built_at(path))

    def schedule(self, competition: str) -> pd.DataFrame:
        """Every scheduled match of the league in the dataset, earliest first.

        Unlike :meth:`upcoming` this keeps matches dated before today, which
        may be played but not yet in the results data.
        """
        rows = self._frame[self._frame["competition"] == competition]
        return rows[["match_date", "kickoff", "home_team", "away_team", "round"]]

    def upcoming(self, competition: str, limit: int) -> FixturesResponse:
        """The league's next ``limit`` fixtures from today on, earliest first."""
        today = self._today().isoformat()
        rows = self._frame[
            (self._frame["competition"] == competition)
            & (self._frame["match_date"] >= today)
        ].head(limit)
        fixtures = [
            Fixture(
                match_date=date.fromisoformat(str(row["match_date"])),
                kickoff=_kickoff(str(row["kickoff"])),
                home_team=str(row["home_team"]),
                away_team=str(row["away_team"]),
                round=str(row["round"]),
            )
            for row in rows.to_dict("records")
        ]
        return FixturesResponse(
            competition=competition, fixtures=fixtures, updated_at=self.updated_at
        )


def _kickoff(value: str) -> datetime | None:
    """Parse a stored kick-off; an empty cell means the time is not confirmed."""
    return datetime.fromisoformat(value) if value else None
