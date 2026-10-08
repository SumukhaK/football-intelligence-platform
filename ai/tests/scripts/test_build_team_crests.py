"""Tests for matching snapshot crests to canonical team names."""

from __future__ import annotations

import pandas as pd

from scripts.build_team_crests import match_crests

A, B, C = (f"https://crests.football-data.org/{n}.png" for n in (1, 2, 3))


def games(*rows: tuple[str, int, int, str, str]) -> pd.DataFrame:
    columns = ["date", "home_goals", "away_goals", "home_crest", "away_crest"]
    return pd.DataFrame(rows, columns=columns).assign(competition="Serie A")


def results(*rows: tuple[str, str, str, int, int]) -> pd.DataFrame:
    columns = [
        "match_date",
        "home_team",
        "away_team",
        "full_time_home_goals",
        "full_time_away_goals",
    ]
    return pd.DataFrame(rows, columns=columns).assign(competition="Serie A")


def test_results_and_anchored_fixtures_find_every_crest() -> None:
    snapshot = games(
        ("2025-01-05", 2, 1, A, B),
        # A day later in UTC than our local date; still matched.
        ("2025-01-13", 0, 0, B, A),
        ("2026-09-01", None, None, C, A),
    )
    played = results(
        ("2025-01-05", "Inter", "Roma", 2, 1),
        ("2025-01-12", "Roma", "Inter", 0, 0),
    )
    upcoming = pd.DataFrame(
        {
            "competition": ["Serie A"],
            "match_date": ["2026-09-01"],
            "home_team": ["Venezia"],
            "away_team": ["Inter"],
        }
    )
    assert match_crests(played, upcoming, snapshot) == {
        "Inter": A,
        "Roma": B,
        "Venezia": C,
    }
