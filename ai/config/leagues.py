"""League structure for the top five European leagues (ADR 005).

Team counts change over time, so each division lists the first season from
which a count applies. Season codes use football-data.co.uk's four-digit form,
e.g. ``"0001"`` for 2000/01.
"""

from __future__ import annotations

from typing import Final

TOP_FIVE_DIVISIONS: Final[tuple[str, ...]] = ("E0", "D1", "SP1", "I1", "F1")

# (first season start year, team count), ordered by start year.
_TEAM_COUNT_HISTORY: Final[dict[str, tuple[tuple[int, int], ...]]] = {
    "E0": ((1995, 20),),
    "D1": ((1965, 18),),
    "SP1": ((1997, 20),),
    "I1": ((1988, 18), (2004, 20)),
    "F1": ((1997, 18), (2002, 20), (2023, 18)),
}

# Seasons that legitimately ended early, keyed by (division, season code).
KNOWN_INCOMPLETE_SEASONS: Final[dict[tuple[str, str], int]] = {
    # Ligue 1 2019/20 was abandoned in March 2020 because of COVID-19.
    ("F1", "1920"): 279,
}


def season_start_year(code: str) -> int:
    """Return the calendar year a season code starts in, e.g. ``"0001"`` → 2000."""
    _check_code(code)
    first = int(code[:2])
    return 1900 + first if first >= 50 else 2000 + first


def season_codes(first: str, last: str) -> list[str]:
    """Return every season code from ``first`` to ``last`` inclusive."""
    start, end = season_start_year(first), season_start_year(last)
    if end < start:
        raise ValueError(f"Season range is reversed: {first!r} to {last!r}")
    return [f"{y % 100:02d}{(y + 1) % 100:02d}" for y in range(start, end + 1)]


def expected_team_count(division: str, season_code: str) -> int:
    """Return how many teams played in ``division`` during ``season_code``."""
    year = season_start_year(season_code)
    count = None
    for from_year, teams in _TEAM_COUNT_HISTORY[division]:
        if year >= from_year:
            count = teams
    if count is None:
        raise ValueError(f"No team count recorded for {division} {season_code}")
    return count


def expected_match_count(division: str, season_code: str) -> int:
    """Return the number of league matches expected in a season."""
    incomplete = KNOWN_INCOMPLETE_SEASONS.get((division, season_code))
    if incomplete is not None:
        return incomplete
    teams = expected_team_count(division, season_code)
    return teams * (teams - 1)


def _check_code(code: str) -> None:
    """Raise ``ValueError`` unless ``code`` is a valid consecutive season code."""
    valid = len(code) == 4 and code.isdigit()
    if not valid or (int(code[:2]) + 1) % 100 != int(code[2:]):
        raise ValueError(f"Invalid season code: {code!r}")
