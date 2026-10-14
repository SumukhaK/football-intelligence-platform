"""Tests for backend.app.services.outlook_service (ADR 023)."""

from __future__ import annotations

from datetime import date
from itertools import permutations
from typing import Any

import pandas as pd
import pytest

from backend.app.exceptions import SeasonOutlookNotAvailableError, UnknownTeamError
from backend.app.services import outlook_service
from backend.app.services.outlook_service import OutlookService
from goals.dixon_coles import DixonColesParams, fit_dixon_coles
from goals.insights import team_strengths

PL = "Premier League"
TEAMS = ["Arsenal", "Brentford", "Chelsea", "Fulham"]
TODAY = date(2026, 8, 27)  # a Thursday
SIMS = 200


def _match(day: str, season: str, home: str, away: str, hg: int, ag: int) -> dict:
    return {
        "match_date": day,
        "season": season,
        "competition": PL,
        "home_team": home,
        "away_team": away,
        "full_time_home_goals": hg,
        "full_time_away_goals": ag,
    }


def _last_season() -> list[dict]:
    """A double round robin in 2025/26 so the goals model has data to fit."""
    rows = []
    for i, (home, away) in enumerate(permutations(TEAMS, 2)):
        day = (pd.Timestamp("2025-09-01") + pd.Timedelta(days=14 * i)).date()
        rows.append(_match(str(day), "2025/26", home, away, (i * 7) % 4, (i * 3) % 3))
    return rows


# This season: week one Sat/Sun, week two Sat and a Monday match.
PLAYED = [
    _match("2026-08-15", "2026/27", "Arsenal", "Brentford", 2, 0),
    _match("2026-08-16", "2026/27", "Chelsea", "Fulham", 1, 1),
    _match("2026-08-22", "2026/27", "Brentford", "Chelsea", 0, 1),
    _match("2026-08-24", "2026/27", "Fulham", "Arsenal", 0, 3),
]
DONE = {(m["home_team"], m["away_team"]) for m in PLAYED}
MATCHES = pd.DataFrame(_last_season() + PLAYED)


def _schedule(extra: frozenset[tuple[str, str]] = frozenset()) -> pd.DataFrame:
    pairs = [p for p in permutations(TEAMS, 2) if p not in DONE or p in extra]
    # One fixture already in the results, which must not be played twice.
    pairs.append(("Arsenal", "Brentford"))
    return pd.DataFrame(
        [("2026-09-12", "", h, a, "MD") for h, a in pairs],
        columns=["match_date", "kickoff", "home_team", "away_team", "round"],
    )


def _params(before: date = TODAY) -> DixonColesParams:
    return fit_dixon_coles(MATCHES, pd.Timestamp(before), competition=PL)


def _service(matches: pd.DataFrame = MATCHES) -> OutlookService:
    return OutlookService(matches, today=lambda: TODAY, history_simulations=SIMS)


def _outlook(team: str = "Arsenal", service: OutlookService | None = None) -> Any:
    service = service or _service()
    return service.outlook(team, PL, _schedule(), _params(), "dc-test")


def test_projection_describes_the_team() -> None:
    result = _outlook()
    assert (result.team, result.competition, result.season) == (
        "Arsenal",
        PL,
        "2026/27",
    )
    assert result.projection.team == "Arsenal"
    assert result.projection.current_points == 6
    assert 0.0 <= result.projection.chance_first <= 1.0
    assert result.model_version == "dc-test"
    assert result.as_of == TODAY


def test_table_lists_every_team_best_first() -> None:
    table = _outlook().table
    assert sorted(row.team for row in table) == TEAMS
    expected = [row.expected_points for row in table]
    assert expected == sorted(expected, reverse=True)
    assert sum(row.chance_first for row in table) == pytest.approx(1.0, abs=0.01)


def test_strengths_match_the_goals_model() -> None:
    params = _params()
    result = _service().outlook("Chelsea", PL, _schedule(), params, "dc-test")
    expected = team_strengths(params, "Chelsea", "Chelsea")
    assert result.strengths.attack == pytest.approx(expected.home_attack)
    assert result.strengths.defence == pytest.approx(expected.home_defence)


def test_history_has_a_start_point_and_one_per_finished_week() -> None:
    history = _outlook().history
    # The week with a Monday match ends on 31 Aug, after today, so it is left out.
    assert [p.as_of for p in history] == [
        date(2026, 8, 14),
        date(2026, 8, 16),
        date(2026, 8, 23),
    ]
    # Fulham v Arsenal was on a Monday, so it counts towards the next week.
    assert [p.played for p in history] == [0, 1, 1]


def test_history_points_use_only_what_was_known_then() -> None:
    """A point equals one computed from data that ended at its cutoff."""
    cutoff = date(2026, 8, 17)
    known = MATCHES[pd.to_datetime(MATCHES["match_date"]).dt.date < cutoff]
    later = DONE - {("Arsenal", "Brentford"), ("Chelsea", "Fulham")}
    service = _service(known)
    then = service.outlook(
        "Arsenal", PL, _schedule(extra=frozenset(later)), _params(), "dc"
    )
    now = _outlook()
    assert then.history[1] == now.history[1]


def test_league_points_are_cached_across_teams(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[pd.Timestamp] = []

    def counting_fit(*args: Any, **kwargs: Any) -> DixonColesParams:
        calls.append(args[1])
        return fit_dixon_coles(*args, **kwargs)

    monkeypatch.setattr(outlook_service, "fit_dixon_coles", counting_fit)
    service = _service()
    _outlook("Arsenal", service)
    _outlook("Fulham", service)
    assert len(calls) == 3


def test_unknown_team_is_rejected() -> None:
    with pytest.raises(UnknownTeamError):
        _outlook("Real Madrid")


def test_league_without_history_is_not_available() -> None:
    with pytest.raises(SeasonOutlookNotAvailableError):
        _service().outlook("Arsenal", "Serie A", _schedule(), _params(), "dc")
