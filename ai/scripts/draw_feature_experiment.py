"""Experiment: do draw-oriented features improve the match model?

Adds six candidate features to the current feature matrix, retrains with the
served model's configuration, and compares log loss with a paired bootstrap on
the test season and the holdout seasons. The features are built here rather
than in ``feature_engineering`` because they were not adopted; see
``docs/reports/draw-handling.md``.

Usage:
    uv run python -m scripts.draw_feature_experiment
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from evaluation.comparison import paired_bootstrap_delta
from feature_engineering.base import build_team_match_view
from training.configuration import TrainingConfig
from training.persistence import load_json
from training.splitter import SeasonSplitter, get_feature_columns
from training.trainer import ModelTrainer, TrainedModel

MATRIX = Path("../datasets/features/top5/feature_matrix.parquet")
CONFIG = Path("models/latest/config.json")
LEAGUE_WINDOW = 760  # about two seasons of one league's matches


def draw_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the six candidate features from matches before each one."""
    tv = build_team_match_view(df)
    tv["total_goals"] = tv["goals_scored"] + tv["goals_conceded"]
    by_team = tv.groupby("team")
    for column, source in [("draw_rate", "draw"), ("total_goals", "total_goals")]:
        tv[f"{column}_last10"] = by_team[source].transform(
            lambda s: s.shift(1).rolling(10, min_periods=1).mean()
        )
    home = tv[tv["is_home"]].set_index("_original_idx")
    away = tv[~tv["is_home"]].set_index("_original_idx")
    out = pd.DataFrame(index=df.index)
    for side, view in [("home", home), ("away", away)]:
        out[f"{side}_draw_rate_last10"] = view["draw_rate_last10"]
        out[f"{side}_total_goals_last10"] = view["total_goals_last10"]
    out["elo_gap_abs"] = (df["home_elo_before"] - df["away_elo_before"]).abs()
    drew = (df["result"] == "D").astype(float)
    out["league_draw_rate"] = drew.groupby(df["competition"]).transform(
        lambda s: s.shift(1).rolling(LEAGUE_WINDOW, min_periods=50).mean()
    )
    return out


def fit(frame: pd.DataFrame, config: TrainingConfig) -> tuple[TrainedModel, list[str]]:
    """Train on the configured season split and return the model and columns."""
    columns = get_feature_columns(frame, config)
    split = SeasonSplitter().split(frame, columns, config)
    return ModelTrainer().train(split, config), columns


def main(argv: list[str] | None = None) -> int:
    """Print the log-loss difference, new minus current, per season block."""
    argparse.ArgumentParser(
        prog="scripts.draw_feature_experiment",
        description="Compare the served model with and without draw features.",
    ).parse_args(argv)
    config = TrainingConfig(**load_json(CONFIG))
    df = pd.read_parquet(MATRIX)
    df = df.sort_values(["match_date", "competition", "home_team"], kind="stable")
    df = df.reset_index(drop=True)
    extended = pd.concat([df, draw_features(df)], axis=1)
    current, current_cols = fit(df, config)
    candidate, candidate_cols = fit(extended, config)
    for block, seasons in [
        ("test", config.test_seasons),
        ("holdout", config.holdout_seasons),
    ]:
        rows = extended[extended[config.season_column].isin(seasons)]
        _, p_current = ModelTrainer().predict(current, rows[current_cols])
        _, p_candidate = ModelTrainer().predict(candidate, rows[candidate_cols])
        delta = paired_bootstrap_delta(
            rows["result"].to_numpy(), p_candidate, p_current, current.classes
        )
        print(
            f"{block}: log loss change {delta.mean:+.4f} "
            f"(95% interval {delta.lower:+.4f} to {delta.upper:+.4f})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
