"""Crest and emblem image URLs by team or league name (ADR 020)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class CrestTable:
    """Looks up an image URL in a ``name,crest_url`` reference table."""

    def __init__(self, urls: dict[str, str]) -> None:
        """Initialise with name → image URL."""
        self._urls = urls

    @classmethod
    def from_csv(cls, path: Path) -> CrestTable:
        """Load and validate a crest table.

        Raises:
            ValueError: If a name is listed twice or a URL is not https.
        """
        table = pd.read_csv(path, dtype=str)
        if table["name"].duplicated().any():
            raise ValueError(f"Duplicate name in {path}")
        if not table["crest_url"].str.startswith("https://").all():
            raise ValueError(f"Non-https crest URL in {path}")
        return cls(dict(zip(table["name"], table["crest_url"], strict=True)))

    def url(self, name: str) -> str | None:
        """The image URL for ``name``, or None when it has none."""
        return self._urls.get(name)
