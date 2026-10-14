"""Score the served model on a season in progress, match by match.

Each played match of the season is predicted with features built only from
matches before it: the in-progress results are appended to the completed
history and run through the same feature pipeline used for training. The model
is not retrained, so every prediction is genuinely out of sample.

The bookmaker forecast is Bet365's pre-match odds with the margin removed. It
is a benchmark only and never a model input. The Elo-only baseline shows how
much the model adds over the rating gap alone.

The command-line entry point is ``evaluation.in_season_cli``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from evaluation.compare_models import score_block
from evaluation.comparison import (
    bootstrap_interval,
    class_prior_probabilities,
    implied_probabilities,
    paired_bootstrap_delta,
)
from feature_engineering.pipeline import FeaturePipeline

BOOTSTRAP_METRICS = ["accuracy", "log_loss", "rps", "brier"]
_ODDS = ["home_odds", "draw_odds", "away_odds"]


def build_season_features(
    history: pd.DataFrame, current: pd.DataFrame, work_dir: Path
) -> pd.DataFrame:
    """Run the feature pipeline over history plus the current season.

    Returns the whole feature matrix; each row's features come only from
    matches before it. ``split_season`` separates history from the season.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    combined_path = work_dir / "matches_with_current_season.csv"
    pd.concat([history, current], ignore_index=True).to_csv(combined_path, index=False)
    FeaturePipeline().run(combined_path, work_dir / "features")
    return pd.read_parquet(work_dir / "features" / "feature_matrix.parquet")


def split_season(
    matrix: pd.DataFrame, season: str, through: str | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (earlier seasons, the season's matches up to ``through``)."""
    # Season labels are "YYYY/YY", so string order is chronological order.
    history = matrix[matrix["season"] < season]
    keep = matrix["season"] == season
    if through is not None:
        keep &= pd.to_datetime(matrix["match_date"]) <= pd.Timestamp(through)
    rows = matrix[keep].sort_values(["match_date", "competition", "home_team"])
    return history.reset_index(drop=True), rows.reset_index(drop=True)


def elo_baseline(
    history: pd.DataFrame, rows: pd.DataFrame, classes: list[str]
) -> np.ndarray:
    """Forecast from the pre-match Elo gap alone, fitted on earlier seasons.

    A multinomial logistic regression on home minus away Elo; its intercept
    carries home advantage.
    """
    model = LogisticRegression().fit(_elo_gap(history), history["result"])
    probs = model.predict_proba(_elo_gap(rows))
    return np.asarray(probs[:, [list(model.classes_).index(c) for c in classes]])


def evaluate_season(
    rows: pd.DataFrame, probs: np.ndarray, history: pd.DataFrame, classes: list[str]
) -> dict[str, Any]:
    """Score model, Elo-only, priors and bookmaker, with bootstrap ranges.

    ``scores`` is per league. ``intervals`` are overall 95% bootstrap ranges,
    and ``deltas`` are paired bootstraps of the model minus each benchmark.
    """
    forecasts = {
        "candidate": probs,
        "elo": elo_baseline(history, rows, classes),
        "priors": class_prior_probabilities(history["result"], len(rows), classes),
    }
    return {
        "scores": score_block(rows, forecasts, classes),
        **_bootstrap(rows, forecasts, classes),
    }


def _bootstrap(
    rows: pd.DataFrame, forecasts: dict[str, np.ndarray], classes: list[str]
) -> dict[str, Any]:
    """Bootstrap the model, Elo-only and bookmaker on matches that have odds."""
    has_odds = rows[_ODDS].notna().all(axis=1).to_numpy()
    y = rows["result"].to_numpy()[has_odds]
    probs = {n: forecasts[n][has_odds] for n in ["candidate", "elo"]}
    probs["bookmaker"] = implied_probabilities(rows[has_odds], classes)
    intervals = {
        name: {
            m: bootstrap_interval(y, p, classes, metric=m) for m in BOOTSTRAP_METRICS
        }
        for name, p in probs.items()
    }
    deltas = {
        f"candidate_minus_{other}": {
            m: paired_bootstrap_delta(
                y, probs["candidate"], probs[other], classes, metric=m
            ).__dict__
            for m in BOOTSTRAP_METRICS
        }
        for other in ["bookmaker", "elo"]
    }
    return {"intervals": intervals, "deltas": deltas}


def _elo_gap(df: pd.DataFrame) -> np.ndarray:
    """Home minus away pre-match Elo, in hundreds of points, as one column."""
    gap = (df["home_elo_before"] - df["away_elo_before"]).to_numpy(dtype=float)
    return gap[:, None] / 100.0


def match_predictions(
    rows: pd.DataFrame, probs: np.ndarray, classes: list[str]
) -> pd.DataFrame:
    """Return one line per match: teams, probabilities, pick and actual result."""
    table = rows[["match_date", "competition", "home_team", "away_team"]].copy()
    for i, cls in enumerate(classes):
        table[f"p_{cls}"] = probs[:, i].round(3)
    table["predicted"] = np.asarray(classes)[probs.argmax(axis=1)]
    table["actual"] = rows["result"].to_numpy()
    table["correct"] = table["predicted"] == table["actual"]
    return table.sort_values(["match_date", "competition", "home_team"])
