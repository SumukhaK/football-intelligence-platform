"""Crest image URLs per canonical team name (ADR 020)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class TeamCrests:
    """Looks up a team's crest URL in the ``team_crests.csv`` reference table."""

    def __init__(self, urls: dict[str, str]) -> None:
        """Initialise with canonical team name → crest URL."""
        self._urls = urls

    @classmethod
    def from_csv(cls, path: Path) -> TeamCrests:
        """Load and validate the crest table.

        Raises:
            ValueError: If a team is listed twice or a URL is not https.
        """
        table = pd.read_csv(path, dtype=str)
        if table["canonical_name"].duplicated().any():
            raise ValueError(f"Duplicate team in {path}")
        if not table["crest_url"].str.startswith("https://").all():
            raise ValueError(f"Non-https crest URL in {path}")
        return cls(dict(zip(table["canonical_name"], table["crest_url"], strict=True)))

    def url(self, team: str) -> str | None:
        """The team's crest URL, or None when it has none."""
        return self._urls.get(team)
