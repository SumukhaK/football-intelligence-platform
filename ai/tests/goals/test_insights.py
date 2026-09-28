"""Tests for fixture insights built from a fitted goals model."""

from __future__ import annotations

import pytest

from goals.dixon_coles import DixonColesParams
from goals.insights import (
    TeamStrengths,
    fixture_insight,
    strength_reasons,
    team_strengths,
)


def params() -> DixonColesParams:
    return DixonColesParams(
        competition="Premier League",
        attack={"Arsenal": 0.32, "Chelsea": 0.05, "Luton": -0.30},
        defence={"Arsenal": 0.25, "Chelsea": 0.02, "Luton": -0.35},
        intercept=0.15,
        home_advantage=0.20,
        rho=-0.08,
        newcomer_attack=-0.25,
        newcomer_defence=-0.30,
        fitted_before="2026-09-28",
        n_matches=1520,
    )


def test_insight_is_consistent() -> None:
    insight = fixture_insight(params(), "Arsenal", "Chelsea")
    total = insight.probability_home + insight.probability_draw
    assert total + insight.probability_away == pytest.approx(1.0)
    assert insight.expected_home_goals > insight.expected_away_goals
    assert len(insight.top_scores) == 5
    assert insight.markets.over_1_5 > insight.markets.over_2_5


def test_strengths_are_multiples_of_an_average_side() -> None:
    s = team_strengths(params(), "Arsenal", "Luton")
    assert s.home_attack > 1 > s.away_attack
    assert s.home_defence < 1 < s.away_defence


def test_unknown_teams_use_the_newcomer_prior() -> None:
    s = team_strengths(params(), "Coventry", "Arsenal")
    assert s.home_attack == pytest.approx(0.7788, abs=1e-4)


def test_reasons_lead_with_the_biggest_effect() -> None:
    s = TeamStrengths(
        home_attack=1.38, home_defence=0.79, away_attack=1.02, away_defence=1.15
    )
    reasons = strength_reasons(s, "Arsenal", "Chelsea")
    assert reasons[0] == (
        "Arsenal score 38% more goals than an average side in this league"
    )
    assert reasons[1] == (
        "Arsenal concede 21% fewer goals than an average side in this league"
    )
    assert len(reasons) == 3
    assert not any("Chelsea score" in r for r in reasons)


def test_average_teams_get_no_reasons() -> None:
    s = TeamStrengths(1.01, 0.99, 1.0, 1.02)
    assert strength_reasons(s, "A", "B") == []
