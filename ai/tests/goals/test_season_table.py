"""Tests for goals.season_table."""

from __future__ import annotations

import pandas as pd
import pytest

from goals.dixon_coles import DixonColesParams
from goals.season_table import project_table, standings


def _results(rows: list[tuple[str, str, int, int]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=[
            "home_team",
            "away_team",
            "full_time_home_goals",
            "full_time_away_goals",
        ],
    )


def _params() -> DixonColesParams:
    return DixonColesParams(
        competition="Premier League",
        attack={"Arsenal": 0.6, "Chelsea": 0.0, "Luton": -0.6},
        defence={"Arsenal": 0.6, "Chelsea": 0.0, "Luton": -0.6},
        intercept=0.15,
        home_advantage=0.20,
        rho=-0.08,
        newcomer_attack=-0.25,
        newcomer_defence=-0.30,
        fitted_before="2026-10-01",
        n_matches=100,
    )


def test_standings_counts_points_and_goals() -> None:
    """Three points for a win, one for a draw, totals per team."""
    table = standings(
        _results([("Arsenal", "Chelsea", 2, 0), ("Chelsea", "Luton", 1, 1)])
    )
    # Chelsea and Luton both have 1 point; Luton's goal difference is better.
    assert list(table.index) == ["Arsenal", "Luton", "Chelsea"]
    assert table.loc["Arsenal", "points"] == 3
    assert table.loc["Chelsea", "points"] == 1
    assert table.loc["Chelsea", "goal_difference"] == -2
    assert table.loc["Luton", "played"] == 1
    assert list(table["position"]) == [1, 2, 3]


def test_standings_breaks_ties_on_goal_difference_then_goals() -> None:
    """Equal points are ordered by goal difference, then goals scored."""
    table = standings(
        _results([("Arsenal", "Luton", 3, 0), ("Chelsea", "Luton", 1, 0)])
    )
    assert list(table.index[:2]) == ["Arsenal", "Chelsea"]


def test_standings_includes_teams_yet_to_play() -> None:
    """A team with no results yet appears with zero points."""
    table = standings(_results([("Arsenal", "Chelsea", 1, 0)]), teams=["Luton"])
    assert table.loc["Luton", "points"] == 0


def test_projection_with_no_fixtures_is_the_current_table() -> None:
    """Nothing left to play means expected points equal current points."""
    table = standings(_results([("Arsenal", "Chelsea", 2, 0)]), teams=["Luton"])
    projected = project_table(
        table, _results([])[["home_team", "away_team"]], _params(), 100
    )
    assert projected.loc["Arsenal", "expected_points"] == 3
    assert projected.loc["Arsenal", "chance_first"] == 1.0


def test_projection_favours_the_stronger_team_and_is_repeatable() -> None:
    """The strongest side leads on expected points; the same seed repeats."""
    table = standings(_results([]), teams=["Arsenal", "Chelsea", "Luton"])
    fixtures = pd.DataFrame(
        [("Arsenal", "Luton"), ("Luton", "Chelsea"), ("Chelsea", "Arsenal")] * 4,
        columns=["home_team", "away_team"],
    )
    first = project_table(table, fixtures, _params(), simulations=2000)
    again = project_table(table, fixtures, _params(), simulations=2000)
    assert first.index[0] == "Arsenal"
    chance_first = first["chance_first"]
    assert chance_first["Arsenal"] > chance_first["Luton"]
    assert first.equals(again)
    assert first["chance_first"].sum() == pytest.approx(1.0, abs=0.01)


def test_standings_counts_clean_sheets() -> None:
    """A match without conceding is a clean sheet."""
    table = standings(
        _results([("Arsenal", "Chelsea", 2, 0), ("Chelsea", "Arsenal", 1, 1)])
    )
    assert table.loc["Arsenal", "clean_sheets"] == 1
    assert table.loc["Chelsea", "clean_sheets"] == 0


def test_projection_reports_goals_and_clean_sheets() -> None:
    """The strongest side is likeliest to score most and keep most clean sheets."""
    table = standings(_results([]), teams=["Arsenal", "Chelsea", "Luton"])
    fixtures = pd.DataFrame(
        [("Arsenal", "Luton"), ("Luton", "Chelsea"), ("Chelsea", "Arsenal")] * 4,
        columns=["home_team", "away_team"],
    )
    projected = project_table(table, fixtures, _params(), simulations=2000)
    most_goals = projected["chance_most_goals"]
    assert most_goals.idxmax() == "Arsenal"
    assert most_goals.sum() == pytest.approx(1.0, abs=0.01)
    assert projected["chance_most_clean_sheets"].idxmax() == "Arsenal"
    goals = projected["expected_goals_for"]
    assert goals["Arsenal"] > goals["Luton"]
    assert (projected["expected_clean_sheets"] >= 0).all()
