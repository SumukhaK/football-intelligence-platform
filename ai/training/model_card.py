"""Model card generation for trained match outcome models."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from evaluation.reports import EvaluationReport
from training.configuration import TrainingConfig
from training.trainer import TrainedModel


def describe_dataset(df: pd.DataFrame, config: TrainingConfig) -> str:
    """Summarise competitions, seasons and match count of a feature matrix."""
    competitions = ", ".join(sorted(df["competition"].astype(str).unique()))
    seasons = sorted(df[config.season_column].astype(str).unique())
    span = seasons[0] if len(seasons) == 1 else f"{seasons[0]} to {seasons[-1]}"
    return f"{competitions}; {span} ({len(df)} matches)"


def describe_split(config: TrainingConfig) -> str:
    """Describe how rows were divided into train, validation and test sets."""
    if config.split_strategy == "season":
        holdout = ", ".join(config.holdout_seasons) or "none"
        return (
            f"Season split (ADR 007): validation {', '.join(config.val_seasons)}; "
            f"test {', '.join(config.test_seasons)}; holdout {holdout}"
        )
    return (
        f"Chronological split (ADR 003): {config.train_ratio:.0%} train, "
        f"{config.val_ratio:.0%} validation, remainder test"
    )


def write_model_card(
    *,
    model: TrainedModel,
    report: EvaluationReport,
    version: str,
    dataset: str,
    config: TrainingConfig,
    output_path: Path,
) -> None:
    """Write a model_card.md describing the trained model."""
    tm = report.test_metrics
    cv = report.cv_report
    cv_kind = (
        "season walk-forward"
        if config.split_strategy == "season"
        else ("TimeSeriesSplit")
    )
    card = f"""# Model Card — Football Match Outcome Predictor

## Model Name
`football-outcome-xgboost-{version}`

## Purpose
Multi-class classification: Home win (H), Draw (D), or Away win (A).

## Intended Use
- Input to the Football Intelligence Platform prediction API.
- Research and demonstration of AI engineering practices.
- Not intended for gambling or commercial deployment.

## Training Dataset
- Source: {dataset}
- Split: {describe_split(config)}
- Feature matrix: {report.n_features} pre-match engineered features
- Post-match statistics and betting odds are excluded to prevent data leakage.

## Feature Set
- Rolling form (wins, points over last 5 and 10 matches)
- Goal statistics (scored, conceded, difference)
- Home advantage and away form (expanding window)
- Rest days since last match in the same season
- Head-to-head history
- League position, points, matches played at the start of the match day
- Elo ratings per league (K=32, start=1500, carried across seasons)
- Strength of schedule (rolling opponent Elo)

## Training Configuration
- Algorithm: XGBoost (multi:softprob)
- Best iteration: {model.best_iteration}
- Classes: {", ".join(model.classes)}
- Training rows: {report.n_train}
- Validation rows: {report.n_val}
- Test rows: {report.n_test}

## Evaluation Metrics (Test Set)
| Metric | Value |
|---|---|
| Accuracy | {tm.accuracy:.4f} |
| F1 (weighted) | {tm.f1_weighted:.4f} |
| Log Loss | {tm.log_loss:.4f} |
| ROC AUC (OvR) | {tm.roc_auc_ovr:.4f} |

## Cross-Validation ({cv_kind}, {cv.n_folds} folds)
| Metric | Mean | Std |
|---|---|---|
| Accuracy | {cv.mean_accuracy:.4f} | {cv.std_accuracy:.4f} |
| F1 (weighted) | {cv.mean_f1:.4f} | {cv.std_f1:.4f} |
| Log Loss | {cv.mean_log_loss:.4f} | {cv.std_log_loss:.4f} |

## Known Limitations
- First-match NaN values for rolling features are imputed with training-set medians.
- Elo pools are per league, so ratings are not comparable across leagues.

## Failure Cases
- Teams new to a league start at the average rating of the teams they replaced.
- Unusual rest patterns (mid-season breaks, COVID fixtures) may skew rest-day features.

## Ethical Considerations
- This model predicts sporting outcomes. Do not use it to influence betting markets.
- Predictions carry uncertainty. Do not present them as certainties.
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(card, encoding="utf-8")
