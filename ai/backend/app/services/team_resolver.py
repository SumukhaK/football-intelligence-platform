"""Map the team names people type to the names the data uses.

The chat model passes names as users write them ("Manchester United"), while
the data uses football-data.co.uk names ("Man United"). The openfootball
mapping already lists full club names for every served league.
"""

from __future__ import annotations

import difflib
import re
import unicodedata

from config.team_names import OPENFOOTBALL_TEAM_NAMES

_NOISE = {"fc", "afc", "cf", "sc", "ac", "club", "de", "the"}


class TeamNotFoundError(ValueError):
    """No known team matches the name; carries close suggestions."""


def normalise(name: str) -> str:
    """Lower case, no accents, no punctuation or club suffixes like "FC"."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    words = re.sub(r"[^a-z0-9]+", " ", plain.lower()).split()
    return " ".join(w for w in words if w not in _NOISE)


def resolve_team(name: str, known: list[str]) -> str:
    """The data's name for ``name`` among ``known`` teams.

    Raises:
        TeamNotFoundError: If nothing matches; the message suggests close names.
    """
    keys = _keys(known)
    wanted = normalise(name)
    if wanted in keys:
        return keys[wanted]
    close = difflib.get_close_matches(wanted, keys, n=3, cutoff=0.6)
    suggestions = sorted({keys[c] for c in close})
    hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
    raise TeamNotFoundError(f"No team called '{name}' in this league.{hint}")


def _keys(known: list[str]) -> dict[str, str]:
    """Normalised spelling to data name, for known teams and their full names."""
    keys = {normalise(team): team for team in known}
    for names in OPENFOOTBALL_TEAM_NAMES.values():
        for full, team in names.items():
            if team in known:
                keys.setdefault(normalise(full), team)
    return keys
