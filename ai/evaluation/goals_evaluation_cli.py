"""CLI: tune and evaluate the goals model with a rolling-origin backtest.

Usage:
    uv run python -m evaluation.goals_evaluation_cli
        [--matches CSV] [--model PATH] [--in-season-xgb CSV] [--output-dir DIR]

Steps:
1. Tune the time decay ``xi`` and shrinkage ``l2`` on the validation season.
2. Forecast the test season, the holdout seasons and the season in progress
   with the tuned model and with an independent Poisson baseline (no rho, no
   decay), refitting before every matchweek.
3. Score scorelines, goal markets (against bookmakers' over 2.5 odds) and the
   implied home/draw/away probabilities (against the served XGBoost model).

Writes ``goals_evaluation.json`` and ``goals_forecasts.csv``.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from evaluation.compare_models import predict_probabilities
from evaluation.comparison import paired_bootstrap_delta
from evaluation.goals_backtest import rolling_origin_forecasts
from evaluation.goals_metrics import (
    OUTCOME_CLASSES,
    bootstrap_mean_difference,
    market_comparison,
    outcome_metrics,
    over_2_5_happened,
    reliability,
    scoreline_metrics,
)
from goals.dixon_coles import GoalsModelConfig
from training.persistence import load_json, load_model, save_json

XI_GRID = [0.0, 0.001, 0.002, 0.003, 0.004, 0.005]
L2_GRID = [2.0, 8.0, 16.0, 32.0]
KEY = ["match_date", "home_team", "away_team"]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evaluation.goals_evaluation_cli")
    parser.add_argument("--matches", default=None, help="Live processed CSV")
    parser.add_argument("--model", default="models/latest/model.joblib")
    parser.add_argument(
        "--feature-matrix", default="../datasets/features/top5/feature_matrix.parquet"
    )
    parser.add_argument(
        "--in-season-xgb",
        default="models/backtests/2627_20260928_model123224/predictions.csv",
    )
    parser.add_argument("--in-season", default="2026/27")
    parser.add_argument("--output-dir", default="models/evaluation/goals")
    return parser


def _latest_live(base: Path) -> Path:
    files = sorted(base.glob("match_results_live_v*.csv"))
    if not files:
        raise FileNotFoundError(f"No live dataset in {base}")
    return files[-1]


def forecast_all(
    matches: pd.DataFrame, seasons: list[str], config: GoalsModelConfig
) -> pd.DataFrame:
    """Rolling-origin forecasts for every competition, concatenated."""
    parts = [
        rolling_origin_forecasts(group, seasons, config)
        for _, group in matches.groupby("competition")
    ]
    return pd.concat(parts, ignore_index=True)


def tune(matches: pd.DataFrame, seasons: list[str]) -> tuple[GoalsModelConfig, list]:
    """Pick xi and l2 by scoreline log loss on the validation seasons."""
    trials = []
    for xi, l2 in itertools.product(XI_GRID, L2_GRID):
        config = GoalsModelConfig(xi=xi, l2=l2)
        loss = scoreline_metrics(forecast_all(matches, seasons, config))
        trials.append({"xi": xi, "l2": l2, **loss})
        print(f"  xi={xi} l2={l2}: {loss['scoreline_log_loss']:.4f}", flush=True)
    best = min(trials, key=lambda t: t["scoreline_log_loss"])
    return GoalsModelConfig(xi=best["xi"], l2=best["l2"]), trials


def xgboost_probabilities(args: argparse.Namespace) -> pd.DataFrame:
    """Served-model H/D/A probabilities keyed by match, for every block."""
    model = load_model(Path(args.model))
    config = load_json(Path(args.model).with_name("config.json"))
    matrix = pd.read_parquet(args.feature_matrix)
    seasons = config["test_seasons"] + config["holdout_seasons"]
    rows = matrix[matrix["season"].isin(seasons)]
    probs = predict_probabilities(model, rows)
    table = rows[KEY].copy()
    for i, cls in enumerate(model.classes):
        table[f"xgb_{cls}"] = probs[:, i]
    live = pd.read_csv(args.in_season_xgb)
    live = live.rename(columns={f"p_{c}": f"xgb_{c}" for c in model.classes})
    table = pd.concat([table, live[KEY + [f"xgb_{c}" for c in model.classes]]])
    table["match_date"] = pd.to_datetime(table["match_date"])
    return table


def score_block(
    model: pd.DataFrame, baseline: pd.DataFrame, xgb: pd.DataFrame
) -> dict[str, Any]:
    """All metrics for one block of seasons."""
    joined = model.merge(xgb, on=KEY, how="left")
    has_xgb = joined[[f"xgb_{c}" for c in OUTCOME_CLASSES]].notna().all(axis=1)
    both = joined[has_xgb]
    xgb_probs = both[[f"xgb_{c}" for c in OUTCOME_CLASSES]].to_numpy()
    model_probs = both[[f"p_{c}" for c in OUTCOME_CLASSES]].to_numpy()
    return {
        "matches": int(len(model)),
        "scoreline": {
            "model": scoreline_metrics(model),
            "baseline": scoreline_metrics(baseline),
            "log_loss_change_vs_baseline": bootstrap_mean_difference(
                -np.log(model["p_score"]), -np.log(baseline["p_score"])
            ),
        },
        "markets": market_comparison(model),
        "over_2_5_reliability": reliability(
            model["p_over_2_5"], over_2_5_happened(model)
        ),
        "outcomes": {
            "matches_with_xgboost": int(has_xgb.sum()),
            "goals_model": outcome_metrics(both),
            "xgboost": outcome_metrics(
                both.assign(**{f"p_{c}": both[f"xgb_{c}"] for c in OUTCOME_CLASSES})
            ),
            "log_loss_change_vs_xgboost": vars(
                paired_bootstrap_delta(
                    both["result"], model_probs, xgb_probs, OUTCOME_CLASSES
                )
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    """Tune, backtest and write the report."""
    args = _parser().parse_args(argv)
    path = (
        Path(args.matches)
        if args.matches
        else _latest_live(Path("../datasets/processed/football_data"))
    )
    matches = pd.read_csv(path, parse_dates=["match_date"])
    training = load_json(Path(args.model).with_name("config.json"))
    blocks = {
        "test": training["test_seasons"],
        "holdout": training["holdout_seasons"],
        "in_season": [args.in_season],
    }
    print(f"Tuning on {training['val_seasons']} from {path.name}", flush=True)
    best, trials = tune(matches, training["val_seasons"])
    baseline_config = GoalsModelConfig(xi=0.0, l2=best.l2, fit_rho=False)
    xgb = xgboost_probabilities(args)

    report: dict[str, Any] = {
        "matches_file": path.name,
        "tuning": {"seasons": training["val_seasons"], "trials": trials},
        "config": vars(best),
        "baseline_config": vars(baseline_config),
        "blocks": {},
    }
    forecasts = []
    for name, seasons in blocks.items():
        model = forecast_all(matches, seasons, best)
        baseline = forecast_all(matches, seasons, baseline_config)
        report["blocks"][name] = score_block(model, baseline, xgb)
        forecasts.append(model.assign(block=name))
        print(f"Scored {name}: {len(model)} matches", flush=True)

    out = Path(args.output_dir)
    save_json(report, out / "goals_evaluation.json")
    pd.concat(forecasts).to_csv(out / "goals_forecasts.csv", index=False)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
