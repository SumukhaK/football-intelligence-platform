"""Metrics for goals-model forecasts: scorelines, goal markets and outcomes.

Every function takes the table produced by
``evaluation.goals_backtest.rolling_origin_forecasts`` (or columns of it).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from evaluation.comparison import score_probabilities

OUTCOME_CLASSES = ["A", "D", "H"]
_EPS = 1e-12
RELIABILITY_EDGES = [0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0]


def scoreline_metrics(forecasts: pd.DataFrame) -> dict[str, float]:
    """Exact-score log loss and top-1 / top-3 hit rates."""
    return {
        "scoreline_log_loss": float(
            -np.log(np.clip(forecasts["p_score"], _EPS, None)).mean()
        ),
        "top1_hit_rate": float(forecasts["top1_hit"].mean()),
        "top3_hit_rate": float(forecasts["top3_hit"].mean()),
    }


def binary_scores(prob: pd.Series, happened: pd.Series) -> dict[str, float]:
    """Brier score and log loss for a yes/no event."""
    p = np.clip(prob.to_numpy(dtype=float), _EPS, 1 - _EPS)
    y = happened.to_numpy(dtype=float)
    return {
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
    }


def over_2_5_happened(forecasts: pd.DataFrame) -> pd.Series:
    """True where the match had three or more goals."""
    return (forecasts["home_goals"] + forecasts["away_goals"]) > 2.5


def bookmaker_over_2_5(forecasts: pd.DataFrame) -> pd.Series:
    """Market-average over 2.5 probability with the bookmaker margin removed."""
    over = 1 / forecasts["over_2_5_odds"]
    under = 1 / forecasts["under_2_5_odds"]
    return over / (over + under)


def market_comparison(forecasts: pd.DataFrame) -> dict[str, Any]:
    """Over 2.5 and BTTS scores, with bookmakers on matches that have odds."""
    over = over_2_5_happened(forecasts)
    btts = (forecasts["home_goals"] > 0) & (forecasts["away_goals"] > 0)
    has_odds = forecasts[["over_2_5_odds", "under_2_5_odds"]].notna().all(axis=1)
    priced = forecasts[has_odds]
    return {
        "btts": binary_scores(forecasts["p_btts"], btts),
        "over_2_5": binary_scores(forecasts["p_over_2_5"], over),
        "over_2_5_with_odds": {
            "matches": int(has_odds.sum()),
            "model": binary_scores(priced["p_over_2_5"], over[has_odds]),
            "bookmaker": binary_scores(bookmaker_over_2_5(priced), over[has_odds]),
        },
    }


def reliability(prob: pd.Series, happened: pd.Series) -> list[dict[str, Any]]:
    """Mean forecast against observed frequency, per probability bin."""
    bins = pd.cut(prob, RELIABILITY_EDGES, include_lowest=True)
    frame = pd.DataFrame({"bin": bins, "p": prob, "y": happened.astype(float)})
    grouped = frame.groupby("bin", observed=True).agg(
        matches=("y", "size"), predicted=("p", "mean"), observed=("y", "mean")
    )
    return [
        {
            "bin": str(interval),
            "matches": int(row.matches),
            "predicted": round(float(row.predicted), 3),
            "observed": round(float(row.observed), 3),
        }
        for interval, row in grouped.iterrows()
    ]


def outcome_metrics(forecasts: pd.DataFrame) -> dict[str, float]:
    """Log loss, RPS and Brier of the implied home/draw/away probabilities."""
    probs = forecasts[[f"p_{c}" for c in OUTCOME_CLASSES]].to_numpy()
    scores = score_probabilities(forecasts["result"], probs, OUTCOME_CLASSES)
    return {k: float(v) for k, v in scores.items()}


def bootstrap_mean_difference(
    a: np.ndarray, b: np.ndarray, n_resamples: int = 2000, seed: int = 42
) -> dict[str, float]:
    """Mean and 95% interval of mean(a - b) over paired resamples."""
    diff = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    rng = np.random.default_rng(seed)
    means = np.array(
        [diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(n_resamples)]
    )
    lower, upper = np.percentile(means, [2.5, 97.5])
    return {"mean": float(diff.mean()), "lower": float(lower), "upper": float(upper)}
