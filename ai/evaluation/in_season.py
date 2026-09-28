"""Score the served model on a season in progress, match by match.

Each played match of the season is predicted with features built only from
matches before it: the in-progress results are appended to the completed
history and run through the same feature pipeline used for training. The model
is not retrained, so every prediction is genuinely out of sample.

The command-line entry point is ``evaluation.in_season_cli``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from evaluation.compare_models import score_block
from evaluation.comparison import class_prior_probabilities
from feature_engineering.pipeline import FeaturePipeline


def build_season_features(
    history: pd.DataFrame, current: pd.DataFrame, work_dir: Path
) -> pd.DataFrame:
    """Run the feature pipeline over history plus the current season.

    Returns only the current season's rows, each with features computed from
    matches before it.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    combined_path = work_dir / "matches_with_current_season.csv"
    pd.concat([history, current], ignore_index=True).to_csv(combined_path, index=False)
    FeaturePipeline().run(combined_path, work_dir / "features")
    matrix = pd.read_parquet(work_dir / "features" / "feature_matrix.parquet")
    seasons = set(current["season"])
    return matrix[matrix["season"].isin(seasons)].reset_index(drop=True)


def evaluate_season(
    rows: pd.DataFrame, probs: np.ndarray, history: pd.DataFrame, classes: list[str]
) -> dict[str, Any]:
    """Score model, outcome-frequency priors and bookmakers per league."""
    priors = class_prior_probabilities(history["result"], len(rows), classes)
    return score_block(rows, {"candidate": probs, "priors": priors}, classes)


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
