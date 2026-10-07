# training

XGBoost training pipeline for the match outcome prediction model.

## Packages

| Module | Responsibility |
|---|---|
| `configuration.py` | `TrainingConfig` — hyper-parameters, paths, and the pinned `MODEL_FEATURES` list |
| `splitter.py` | Train/val/test splits; `get_feature_columns` checks the pinned features against the matrix |
| `trainer.py` | `ModelTrainer` — fits XGBClassifier, wraps imputer and label encoder |
| `persistence.py` | Save/load model via joblib; JSON helpers for config and metrics |
| `registry.py` | Register a completed run into the local JSON model registry |
| `model_card.py` | Writes `model_card.md` for each run: data, split, settings, metrics |
| `tuning.py` | Hyperparameter grid search by season walk-forward CV on training seasons only (CLI) |
| `pipeline.py` | `TrainingPipeline` — end-to-end orchestrator; CLI entry point |

## Features

The model trains on exactly the 42 columns in `MODEL_FEATURES`
(`training/configuration.py`), in that order. Training stops with an error if a
pinned feature is missing from the feature matrix, or if the matrix holds a
numeric column that is neither a feature nor listed in `exclude_columns`
(odds, goals, match stats). Adding a feature means adding it to the list on
purpose.

## CLI

Run from `ai/`; paths are relative to it. The five-league model is trained
with the season split (ADR 007):

```bash
uv run python -m training.pipeline --feature-matrix ../datasets/features/top5/feature_matrix.parquet --split-strategy season --val-seasons 2022/23 --test-seasons 2023/24 --holdout-seasons 2024/25 2025/26 --n-estimators 400 --learning-rate 0.03 --max-depth 3 --no-promote
```

Flags:

```
--feature-matrix PATH       Path to feature_matrix.parquet
                            (default: datasets/features/feature_matrix.parquet)
--models-dir DIR            Output root (default: models)
--n-estimators N            Maximum trees; early stopping on validation picks the count (default: 300)
--learning-rate F           XGBoost learning rate (default: 0.1)
--max-depth N               Max tree depth (default: 6)
--seed N                    Random seed (default: 42)
--split-strategy NAME       chronological (70/15/15 by row, ADR 003) or season (ADR 007)
--val-seasons S [S ...]     Season split: early-stopping season(s)
--test-seasons S [S ...]    Season split: test season(s)
--holdout-seasons S [S ...] Season split: seasons never used in training
--no-promote                Write runs/<version> only; leave latest/ and the registry alone
```

Without `--no-promote`, the run replaces `latest/`, which the backend serves.

## Output artifacts

All artifacts are written under `models/`:

```
models/
  registry.json                  # Version index
  latest/                        # Copy of the promoted run (served by the backend)
    model.joblib                 # Trained model (booster + imputer + encoder)
    config.json                  # TrainingConfig used
    metrics.json                 # Train/val/test metrics
    evaluation_report.json       # Full EvaluationReport
    model_card.md                # Human-readable model card
    plots/
      confusion_matrix.png
      feature_importance.png
  runs/<timestamp>/              # Per-run archive (same structure as latest/)
  evaluation/
    evaluation_report.json       # Global copy of latest evaluation
```

## Design decisions

See `docs/adr/001-use-xgboost-for-predictions.md`, `docs/adr/002-joblib-model-serialization.md`,
`docs/adr/003-chronological-train-val-test-split.md` (deprecated) and
`docs/adr/007-season-based-split-and-evaluation.md`.
