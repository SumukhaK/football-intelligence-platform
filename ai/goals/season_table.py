"""League tables: actual standings from results, and projections (ADR 021).

A projection plays every remaining fixture many times with the Dixon-Coles
goals model and adds the simulated points to the real table.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from goals.dixon_coles import DixonColesParams
from goals.score_grid import score_grid

DEFAULT_SIMULATIONS = 10_000
# A fixed seed keeps answers (and tests) repeatable for the same data.
DEFAULT_SEED = 2026
_TABLE_COLUMNS = [
    "played",
    "won",
    "drawn",
    "lost",
    "goals_for",
    "goals_against",
    "clean_sheets",
]
_PROJECTED_COLUMNS = ["points", "goals_for", "goals_against", "clean_sheets"]


def standings(results: pd.DataFrame, teams: list[str] | None = None) -> pd.DataFrame:
    """The league table from played matches, best first.

    ``results`` needs home_team, away_team, full_time_home_goals and
    full_time_away_goals. ``teams`` adds teams that have not played yet.
    Ties are broken by goal difference, then goals scored.
    """
    rows = pd.concat([_side(results, "home"), _side(results, "away")])
    table = rows.groupby("team")[_TABLE_COLUMNS].sum()
    if teams:
        table = table.reindex(sorted(set(table.index) | set(teams)), fill_value=0)
    table["goal_difference"] = table["goals_for"] - table["goals_against"]
    table["points"] = 3 * table["won"] + table["drawn"]
    table = table.sort_values(
        ["points", "goal_difference", "goals_for"], ascending=False, kind="stable"
    )
    table.insert(0, "position", range(1, len(table) + 1))
    return table.astype(int)


def project_table(
    table: pd.DataFrame,
    fixtures: pd.DataFrame,
    params: DixonColesParams,
    simulations: int = DEFAULT_SIMULATIONS,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """Simulate ``fixtures`` on top of ``table`` and summarise the outcome.

    Returns one row per team, best first: current and expected points, the
    most likely position, the chance of finishing first, in the top four and
    in the bottom three, expected goals scored, conceded and clean sheets, and
    the chance of scoring the most goals and keeping the most clean sheets.
    """
    rng = np.random.default_rng(seed)
    index = {team: i for i, team in enumerate(table.index)}
    totals = {
        column: np.tile(table[column].to_numpy(float), (simulations, 1))
        for column in _PROJECTED_COLUMNS
    }
    for home, away in zip(fixtures["home_team"], fixtures["away_team"], strict=True):
        home_goals, away_goals = _sample_scores(params, home, away, simulations, rng)
        _add_result(totals, index[home], home_goals, away_goals)
        _add_result(totals, index[away], away_goals, home_goals)
    return _summary(table, totals)


def _add_result(
    totals: dict[str, np.ndarray], team: int, scored: np.ndarray, conceded: np.ndarray
) -> None:
    totals["points"][:, team] += np.where(scored > conceded, 3, scored == conceded)
    totals["goals_for"][:, team] += scored
    totals["goals_against"][:, team] += conceded
    totals["clean_sheets"][:, team] += conceded == 0


def _positions(totals: dict[str, np.ndarray]) -> np.ndarray:
    """Final position per simulation: points, then goal difference."""
    goal_diff = totals["goals_for"] - totals["goals_against"]
    # Goal difference is scaled well below one point so it only breaks ties.
    order = np.argsort(-(totals["points"] + goal_diff / 1000.0), axis=1)
    positions = np.empty_like(order)
    rows = np.arange(order.shape[0])[:, None]
    positions[rows, order] = np.arange(1, order.shape[1] + 1)
    return positions


def _side(results: pd.DataFrame, side: str) -> pd.DataFrame:
    other = "away" if side == "home" else "home"
    scored = results[f"full_time_{side}_goals"].astype(int)
    conceded = results[f"full_time_{other}_goals"].astype(int)
    return pd.DataFrame(
        {
            "team": results[f"{side}_team"],
            "played": 1,
            "won": (scored > conceded).astype(int),
            "drawn": (scored == conceded).astype(int),
            "lost": (scored < conceded).astype(int),
            "goals_for": scored,
            "goals_against": conceded,
            "clean_sheets": (conceded == 0).astype(int),
        }
    )


def _sample_scores(
    params: DixonColesParams,
    home: str,
    away: str,
    n: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    lam, mu = params.expected_goals(home, away)
    grid = score_grid(lam, mu, params.rho)
    picks = rng.choice(grid.size, size=n, p=grid.ravel())
    return np.divmod(picks, grid.shape[1])


def _summary(table: pd.DataFrame, totals: dict[str, np.ndarray]) -> pd.DataFrame:
    positions = _positions(totals)
    n_teams = positions.shape[1]
    modal = [np.bincount(positions[:, i]).argmax() for i in range(n_teams)]
    summary = pd.DataFrame(
        {
            "current_points": table["points"].to_numpy(),
            "expected_points": totals["points"].mean(axis=0).round(1),
            "most_likely_position": modal,
            "chance_first": (positions == 1).mean(axis=0).round(3),
            "chance_top_four": (positions <= 4).mean(axis=0).round(3),
            "chance_bottom_three": (positions > n_teams - 3).mean(axis=0).round(3),
            "expected_goals_for": totals["goals_for"].mean(axis=0).round(1),
            "expected_goals_against": totals["goals_against"].mean(axis=0).round(1),
            "expected_clean_sheets": totals["clean_sheets"].mean(axis=0).round(1),
            "chance_most_goals": _chance_most(totals["goals_for"]),
            "chance_most_clean_sheets": _chance_most(totals["clean_sheets"]),
        },
        index=table.index,
    )
    return summary.sort_values("expected_points", ascending=False, kind="stable")


def _chance_most(values: np.ndarray) -> np.ndarray:
    """Share of simulations each team leads ``values``; ties split evenly."""
    leaders = values == values.max(axis=1, keepdims=True)
    share = leaders / leaders.sum(axis=1, keepdims=True)
    return np.asarray(share.mean(axis=0).round(3))
