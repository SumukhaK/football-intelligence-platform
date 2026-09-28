"""Compare a candidate model with the current model and baselines (ADR 007).

Usage:
    uv run python -m evaluation.compare_models --candidate-run models/runs/<v>
        [--feature-matrix PATH] [--current-model PATH]
        [--current-feature-matrix PATH]

Writes ``comparison.json`` and ``comparison.md`` into the candidate run
directory. Nothing is promoted; the report ends with the promotion verdict.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from evaluation.comparison import (
    class_prior_probabilities,
    implied_probabilities,
    paired_bootstrap_delta,
    score_probabilities,
)
from evaluation.comparison_report import render_markdown
from training.configuration import TrainingConfig
from training.persistence import load_json, load_model, save_json
from training.splitter import SeasonSplitter
from training.trainer import ModelTrainer, TrainedModel

MATCH_KEY = ["match_date", "home_team", "away_team"]
_ODDS = ["home_odds", "draw_odds", "away_odds"]


def predict_probabilities(model: TrainedModel, df: pd.DataFrame) -> np.ndarray:
    """Return class probabilities in ``model.classes`` order."""
    _, probs = ModelTrainer().predict(model, df[model.feature_names])
    return np.asarray(probs)


def score_block(
    rows: pd.DataFrame,
    forecasts: dict[str, np.ndarray],
    classes: list[str],
    by: str | None = "competition",
) -> dict[str, Any]:
    """Score each forecast overall and per group on rows that have odds."""
    has_odds = rows[_ODDS].notna().all(axis=1).to_numpy()
    rows = rows[has_odds]
    probs = {name: p[has_odds] for name, p in forecasts.items()}
    probs["bookmaker"] = implied_probabilities(rows, classes)
    block: dict[str, Any] = {
        "overall": {
            n: score_probabilities(rows["result"], p, classes) for n, p in probs.items()
        }
    }
    if by is not None:
        results = rows["result"].to_numpy()
        for group, idx in rows.groupby(by).indices.items():
            block[str(group)] = {
                n: score_probabilities(results[idx], p[idx], classes)
                for n, p in probs.items()
            }
    return block


def like_for_like(
    current: TrainedModel,
    candidate: TrainedModel,
    current_df: pd.DataFrame,
    candidate_df: pd.DataFrame,
) -> dict[str, Any]:
    """Score both models on the current model's own test matches.

    The test rows are selected exactly as ``ChronologicalSplitter`` did when
    the current model was trained (ADR 003 defaults).
    """
    config = TrainingConfig()
    ordered = current_df.sort_values(config.date_column).reset_index(drop=True)
    n = len(ordered)
    val_end = int(n * config.train_ratio) + int(n * config.val_ratio)
    test = ordered.iloc[val_end:]
    joined = align_matches(test, candidate_df)
    classes = candidate.classes
    cur = _reorder(predict_probabilities(current, test), current.classes, classes)
    cand = predict_probabilities(candidate, joined)
    block = score_block(joined, {"candidate": cand, "current": cur}, classes, by=None)
    block["delta_log_loss"] = paired_bootstrap_delta(
        joined["result"], cand, cur, classes
    ).__dict__
    block["delta_rps"] = paired_bootstrap_delta(
        joined["result"], cand, cur, classes, metric="rps"
    ).__dict__
    return block


def align_matches(keys: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Return rows of ``df`` for the matches in ``keys``, in ``keys`` order.

    Raises:
        ValueError: If any match in ``keys`` is missing from ``df``.
    """
    left = keys[MATCH_KEY].astype(str).reset_index(drop=True)
    right = df.assign(**{c: df[c].astype(str) for c in MATCH_KEY})
    joined = left.merge(right, on=MATCH_KEY, how="left", validate="one_to_one")
    if joined["result"].isna().any():
        missing = joined.loc[joined["result"].isna(), MATCH_KEY].values.tolist()
        raise ValueError(f"Matches missing from candidate data: {missing}")
    return joined


def verdict(report: dict[str, Any]) -> dict[str, Any]:
    """Apply the ADR 007 promotion rule to a comparison report."""
    delta = report["like_for_like"]["delta_log_loss"]
    checks = {
        "beats_current_on_its_test_matches": delta["upper"] < 0,
        "beats_priors_on_test_seasons": _beats(report["test"], "priors"),
        "beats_priors_on_holdout_seasons": _beats(report["holdout"], "priors"),
    }
    return {"promote": all(checks.values()), "checks": checks}


def _beats(block: dict[str, Any], baseline: str) -> bool:
    """True if the candidate's overall log loss is below ``baseline``'s."""
    overall = block["overall"]
    return bool(overall["candidate"]["log_loss"] < overall[baseline]["log_loss"])


def _reorder(probs: np.ndarray, source: list[str], target: list[str]) -> np.ndarray:
    """Reorder probability columns from ``source`` to ``target`` class order."""
    return probs[:, [source.index(c) for c in target]]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    """Load models and data, then score every comparison."""
    run_dir = Path(args.candidate_run)
    config = TrainingConfig(**load_json(run_dir / "config.json"))
    candidate = load_model(run_dir / "model.joblib")
    df = pd.read_parquet(args.feature_matrix)
    split = SeasonSplitter().split(df, candidate.feature_names, config)
    classes = candidate.classes

    report: dict[str, Any] = {"candidate_run": str(run_dir)}
    for name, seasons in (
        ("test", config.test_seasons),
        ("holdout", config.holdout_seasons),
    ):
        rows = df[df[config.season_column].isin(seasons)]
        report[name] = score_block(
            rows,
            {
                "candidate": predict_probabilities(candidate, rows),
                "priors": class_prior_probabilities(split.y_train, len(rows), classes),
            },
            classes,
        )
    report["like_for_like"] = like_for_like(
        load_model(Path(args.current_model)),
        candidate,
        pd.read_parquet(args.current_feature_matrix),
        df[df["competition"] == "Premier League"],
    )
    report["verdict"] = verdict(report)
    return report


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 when the report is written, 1 on error."""
    parser = argparse.ArgumentParser(prog="evaluation.compare_models")
    parser.add_argument("--candidate-run", required=True)
    parser.add_argument(
        "--feature-matrix", default="../datasets/features/top5/feature_matrix.parquet"
    )
    parser.add_argument("--current-model", default="models/latest/model.joblib")
    parser.add_argument(
        "--current-feature-matrix",
        default="../datasets/features/feature_matrix.parquet",
    )
    args = parser.parse_args(argv)
    try:
        report = build_report(args)
    except Exception as exc:  # noqa: BLE001 — surface any failure as exit code 1
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    run_dir = Path(args.candidate_run)
    save_json(report, run_dir / "comparison.json")
    markdown = render_markdown(report)
    (run_dir / "comparison.md").write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
