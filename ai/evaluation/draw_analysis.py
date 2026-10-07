"""How well does the model see draws, and what would a draw rule cost?

Two questions, answered per season block:

1. Calibration: when the model gives a draw probability of about p, do about
   p of those matches end level?
2. Draw rule: if a draw is picked whenever its probability is within a margin
   of the favourite's, how many draws are caught and how much accuracy is lost?

The margin is read off the validation season only; later seasons show whether
the trade-off holds.

Usage:
    uv run python -m evaluation.draw_analysis
        [--model PATH] [--feature-matrix PATH] [--in-season CSV] [--output PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from evaluation.compare_models import predict_probabilities
from training.persistence import load_json, load_model, save_json

DRAW = "D"
CALIBRATION_EDGES = [0.0, 0.20, 0.24, 0.27, 0.30, 0.33, 1.0]
MARGINS = [0.0, 0.05, 0.09, 0.10, 0.12, 0.15, 0.20]
# ADR 011: the "draw possible" tag and the share of matches it may flag.
TAG_THRESHOLD = 0.28
TAG_MAX_SHARE = 1 / 3


def pick_with_draw_margin(
    probs: np.ndarray, classes: list[str], margin: float
) -> np.ndarray:
    """Pick the most likely outcome, or a draw if it is within ``margin`` of it."""
    labels = np.asarray(classes)[probs.argmax(axis=1)]
    draw = probs[:, classes.index(DRAW)]
    others = np.delete(probs, classes.index(DRAW), axis=1).max(axis=1)
    return np.where(draw >= others - margin, DRAW, labels)


def draw_calibration(
    probs: np.ndarray, y_true: np.ndarray, classes: list[str]
) -> list[dict[str, Any]]:
    """Mean predicted draw probability against the observed draw rate, per bin."""
    draw = probs[:, classes.index(DRAW)]
    bins = pd.cut(draw, CALIBRATION_EDGES, include_lowest=True)
    frame = pd.DataFrame({"bin": bins, "p": draw, "drew": np.asarray(y_true) == DRAW})
    grouped = frame.groupby("bin", observed=True).agg(
        matches=("drew", "size"), predicted=("p", "mean"), observed=("drew", "mean")
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


def draw_rule_tradeoff(
    probs: np.ndarray, y_true: np.ndarray, classes: list[str]
) -> list[dict[str, float]]:
    """Accuracy and share of draws caught for each margin in ``MARGINS``."""
    y = np.asarray(y_true)
    drew = y == DRAW
    rows = []
    for margin in MARGINS:
        picks = pick_with_draw_margin(probs, classes, margin)
        rows.append(
            {
                "margin": margin,
                "accuracy": round(float((picks == y).mean()), 4),
                "draws_caught": round(float((picks[drew] == DRAW).mean()), 4),
                "draw_picks": round(float((picks == DRAW).mean()), 4),
            }
        )
    return rows


def draw_tag(
    probs: np.ndarray, y_true: np.ndarray, classes: list[str], threshold: float
) -> dict[str, float]:
    """Share flagged by the draw tag and the draw rate with and without it."""
    flagged = probs[:, classes.index(DRAW)] >= threshold
    drew = np.asarray(y_true) == DRAW
    return {
        "threshold": threshold,
        "flagged": round(float(flagged.mean()), 4),
        "draw_rate_flagged": (
            round(float(drew[flagged].mean()), 4) if flagged.any() else 0.0
        ),
        "draw_rate_others": (
            round(float(drew[~flagged].mean()), 4) if (~flagged).any() else 0.0
        ),
    }


def lowest_tag_threshold(probs: np.ndarray, classes: list[str]) -> float:
    """Lowest threshold, in 0.01 steps, that flags under a third of matches."""
    draw = probs[:, classes.index(DRAW)]
    for step in range(15, 51):
        if float((draw >= step / 100).mean()) < TAG_MAX_SHARE:
            return step / 100
    return 0.5


def analyse_block(
    probs: np.ndarray, y_true: np.ndarray, classes: list[str]
) -> dict[str, Any]:
    """Calibration and rule trade-off for one block of matches."""
    draw = probs[:, classes.index(DRAW)]
    return {
        "matches": int(len(y_true)),
        "draw_rate": round(float((np.asarray(y_true) == DRAW).mean()), 4),
        "max_draw_probability": round(float(draw.max()), 3),
        "calibration": draw_calibration(probs, y_true, classes),
        "rule": draw_rule_tradeoff(probs, y_true, classes),
        "tag": draw_tag(probs, y_true, classes, TAG_THRESHOLD),
        "lowest_tag_threshold": lowest_tag_threshold(probs, classes),
    }


def _season_blocks(config: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "validation": config["val_seasons"],
        "test": config["test_seasons"],
        "holdout": config["holdout_seasons"],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    """Analyse every season block, plus the in-season predictions if given."""
    model = load_model(Path(args.model))
    config = load_json(Path(args.model).with_name("config.json"))
    matrix = pd.read_parquet(args.feature_matrix)
    report: dict[str, Any] = {"model": str(args.model), "blocks": {}}
    for name, seasons in _season_blocks(config).items():
        rows = matrix[matrix[config["season_column"]].isin(seasons)]
        probs = predict_probabilities(model, rows)
        report["blocks"][name] = analyse_block(
            probs, rows["result"].to_numpy(), model.classes
        )
    if args.in_season:
        table = pd.read_csv(args.in_season)
        probs = table[[f"p_{c}" for c in model.classes]].to_numpy()
        report["blocks"]["in_season"] = analyse_block(
            probs, table["actual"].to_numpy(), model.classes
        )
    return report


def main(argv: list[str] | None = None) -> int:
    """Write the draw analysis report as JSON."""
    parser = argparse.ArgumentParser(prog="evaluation.draw_analysis")
    parser.add_argument("--model", default="models/latest/model.joblib")
    parser.add_argument(
        "--feature-matrix", default="../datasets/features/top5/feature_matrix.parquet"
    )
    parser.add_argument(
        "--in-season", default=None, help="predictions.csv from in_season_cli"
    )
    parser.add_argument("--output", default="models/evaluation/draw_analysis.json")
    args = parser.parse_args(argv)
    report = build_report(args)
    save_json(report, Path(args.output))
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
