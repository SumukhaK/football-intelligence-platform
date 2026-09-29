"""Rolling-origin backtest for the goals model (ADR 009).

Serving refits the goals model whenever results are refreshed, so the
evaluation does the same: before each matchweek (Monday to Sunday) the model
is refitted on every match strictly before that Monday, then that week's
matches are forecast. A single long fit would test a different system from
the one that ships.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd

from goals.dixon_coles import (
    AWAY_GOALS,
    HOME_GOALS,
    DixonColesParams,
    GoalsModelConfig,
    fit_dixon_coles,
)
from goals.score_grid import goal_markets, outcome_probabilities, score_grid

TOP_N = 3


def week_start(dates: pd.Series) -> pd.Series:
    """Monday of each date's week, at midnight."""
    days = pd.to_datetime(dates).dt.normalize()
    return days - pd.to_timedelta(days.dt.weekday, unit="D")


def rolling_origin_forecasts(
    matches: pd.DataFrame,
    seasons: Iterable[str],
    config: GoalsModelConfig,
) -> pd.DataFrame:
    """Forecast every match of ``seasons``, refitting before each matchweek.

    ``matches`` holds one competition's full history (earlier seasons are
    the training data). Returns one row per forecast match.
    """
    matches = matches.assign(match_date=pd.to_datetime(matches["match_date"]))
    targets = matches[matches["season"].isin(list(seasons))]
    rows: list[dict[str, object]] = []
    for start, week in targets.groupby(week_start(targets["match_date"])):
        params = fit_dixon_coles(
            matches, pd.Timestamp(start), config, str(week["competition"].iloc[0])
        )
        rows.extend(_forecast(params, match) for match in week.to_dict("records"))
    return pd.DataFrame(rows)


def _forecast(params: DixonColesParams, match: dict[Any, Any]) -> dict[str, object]:
    home, away = str(match["home_team"]), str(match["away_team"])
    lam, mu = params.expected_goals(home, away)
    grid = score_grid(lam, mu, params.rho)
    x, y = int(match[HOME_GOALS]), int(match[AWAY_GOALS])
    edge = grid.shape[0] - 1
    p_home, p_draw, p_away = outcome_probabilities(grid)
    markets = goal_markets(grid)
    ranked = np.argsort(grid, axis=None)[::-1][:TOP_N]
    actual_cell = np.ravel_multi_index((min(x, edge), min(y, edge)), grid.shape)
    return {
        "match_date": match["match_date"],
        "season": match["season"],
        "competition": match["competition"],
        "home_team": home,
        "away_team": away,
        "home_goals": x,
        "away_goals": y,
        "result": match["result"],
        "fitted_before": params.fitted_before,
        "xg_home": lam,
        "xg_away": mu,
        "p_score": float(grid.flat[actual_cell]),
        "top1_hit": bool(ranked[0] == actual_cell),
        "top3_hit": bool(actual_cell in ranked),
        "p_H": p_home,
        "p_D": p_draw,
        "p_A": p_away,
        "p_over_2_5": markets.over_2_5,
        "p_btts": markets.btts,
        "over_2_5_odds": match.get("over_2_5_odds"),
        "under_2_5_odds": match.get("under_2_5_odds"),
    }
