# training

XGBoost training pipeline for the match outcome prediction model.

## Packages

| Module | Responsibility |
|---|---|
| `configuration.py` | `TrainingConfig` — all hyper-parameters and path settings |
| `splitter.py` | Chronological 70/15/15 train/val/test split |
| `trainer.py` | `ModelTrainer` — fits XGBClassifier, wraps imputer and label encoder |
| `persistence.py` | Save/load model via joblib; JSON helpers for config and metrics |
| `registry.py` | Register a completed run into the local JSON model registry |
| `pipeline.py` | `TrainingPipeline` — end-to-end orchestrator; CLI entry point |

## CLI

Run from the repository root:

```bash
uv run --project ai python -m training.pipeline
```

Optional flags:

```
--feature-matrix PATH   Path to feature_matrix.parquet
--models-dir DIR        Output root (default: models/)
--n-estimators N        Number of trees (default: 300)
--learning-rate F       XGBoost learning rate (default: 0.1)
--max-depth N           Max tree depth (default: 6)
--seed N                Random seed (default: 42)
```

## Output artifacts

All artifacts are written under `models/`:

```
models/
  registry.json                  # Version index
  latest/                        # Symlink-equivalent of last run
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
and `docs/adr/003-chronological-train-val-test-split.md`.
