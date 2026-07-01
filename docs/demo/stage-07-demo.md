# Demo: Stage 7 — Model Training & Evaluation

Demonstrate the complete XGBoost training pipeline: chronological split, early stopping, cross-validation, evaluation, model card, and local registry.

**Approximate demo time:** 5 minutes

---

## Objective

Show that the platform can:
- Train a multi-class XGBoost classifier on a chronological split of the feature matrix.
- Apply early stopping against a validation set to avoid overfitting.
- Run 5-fold `TimeSeriesSplit` cross-validation.
- Generate a full evaluation report with metrics across train, validation, and test splits.
- Produce a human-readable model card automatically.
- Register the run with git commit traceability.
- Do all of this in a single CLI command.

---

## Prerequisites

- `ai/` workspace set up: `uv sync --extra dev`
- Stage 6 complete: `datasets/features/feature_matrix.parquet` must exist.
  - The feature matrix is included in the repository, so Stage 5 and 6 do not need to be re-run for this demo.

---

## Commands

All commands run from the `ai/` directory.

### 1. Show the feature matrix is ready

```sh
# macOS/Linux
ls -la ../datasets/features/

# Windows PowerShell
Get-ChildItem ..\datasets\features\
```

### 2. Show the training tests pass

```sh
uv run pytest tests/training/ tests/evaluation/ tests/inference/ tests/model_registry/ -v
```

Expected: 48 tests pass across 4 packages.

### 3. Run the training pipeline

```sh
uv run python -m training.pipeline
```

This trains the model, evaluates it, and writes all artifacts.

### 4. Show the model card

```sh
# macOS/Linux
cat ../models/latest/model_card.md

# Windows PowerShell
Get-Content ..\models\latest\model_card.md
```

### 5. Show the evaluation report

```sh
uv run python -c "
import json, pathlib
report = json.loads(pathlib.Path('../models/latest/evaluation_report.json').read_text())
test = report['test_metrics']
cv = report['cv_report']
print(f'Test accuracy: {test[\"accuracy\"]:.4f}')
print(f'Test F1:       {test[\"f1_weighted\"]:.4f}')
print(f'Test log-loss: {test[\"log_loss\"]:.4f}')
print(f'CV accuracy:   {cv[\"mean_accuracy\"]:.4f} ± {cv[\"std_accuracy\"]:.4f}')
"
```

### 6. Show the model registry

```sh
# macOS/Linux
cat ../models/registry.json

# Windows PowerShell
Get-Content ..\models\registry.json
```

### 7. Show the feature importance plot

The PNG is written to `models/latest/plots/feature_importance.png`. Open it in any image viewer.

### 8. Load the model and make a prediction

```sh
uv run python -c "
from inference.predictor import MatchPredictor
from pathlib import Path

predictor = MatchPredictor.from_path(Path('../models/latest/model.joblib'))

# Example: predict with some feature values
# (Uses median imputation for any missing values)
prediction = predictor.predict_proba_raw({'home_elo': 1550.0, 'away_elo': 1480.0})
print('Prediction (class probabilities):', prediction)
print('Classes:', predictor.classes)
"
```

---

## Expected Output

```
Feature matrix: .../datasets/features/feature_matrix.parquet
Models dir:     .../models
Estimators:     300  |  LR: 0.1  |  Depth: 6

Version:        <timestamp>
Best iteration: 10
Features used:  42
Test accuracy:  0.5614
Test F1:        0.5181
Test log-loss:  0.9493
Run dir:        models/runs/<timestamp>
```

---

## Verification

After running, confirm:

- [ ] `models/latest/model.joblib` exists
- [ ] `models/latest/model_card.md` exists and contains the training metrics
- [ ] `models/latest/evaluation_report.json` exists
- [ ] `models/registry.json` contains at least one entry with a `git_commit` field
- [ ] `models/latest/plots/feature_importance.png` exists
- [ ] Exit code is 0

---

## What to Highlight

**Architecture points:**
- `TrainingPipeline` composes 6 classes: `TrainingConfig`, `ChronologicalSplitter`, `ModelTrainer`, `CrossValidator`, `EvaluationReport`, and `ModelRegistry`. Each has a single responsibility.
- `TrainingConfig` uses `pydantic-settings` — all hyperparameters are type-validated and can be overridden from environment variables or CLI flags.
- The joblib bundle (`model.joblib`) contains the XGBClassifier, the median imputer, and the label encoder. Loading it with `MatchPredictor.from_path()` gives a fully functional inference object with no pipeline setup required.

**AI engineering points:**
- Chronological split (70/15/15) is non-negotiable: ADR 003 documents why random splitting would constitute temporal leakage. Rows from later in the season cannot inform a model predicting earlier matches.
- Early stopping monitors validation log-loss. The model stopped at iteration 10 out of 300 — the data is small and the model saturates quickly.
- `TimeSeriesSplit` cross-validation respects chronological order within the train+val set. Standard k-fold would allow future-to-past leakage.
- The model card is generated programmatically from the evaluation report — it cannot drift from the actual metrics.
- `registry.json` records the git commit at training time. You can always reproduce a model run by checking out the exact commit and re-running `training.pipeline`.

**Honest metrics:**
- Test accuracy of 56.1% on 380 matches (57 test samples) is competitive for a single-season model with only pre-match features.
- Football match outcomes are genuinely hard to predict. The industry benchmark for this task is approximately 50–55% accuracy with simple models.
- CV accuracy of 44.2% ± 4.7% shows the model struggles on smaller training folds — expected with only one season of data.

---

## Troubleshooting

**`FileNotFoundError: feature_matrix.parquet not found`:** The file is in `datasets/features/`. If running from inside `ai/`, the path `datasets/features/feature_matrix.parquet` resolves relative to `ai/`. Confirm you are in the `ai/` directory.

**Training accuracy is 0.33 (random baseline):** Early stopping may have triggered on iteration 1. This can happen if the validation set contains no examples of one class. With 57 validation rows, class imbalance can be significant — this is a known limitation of training on a single season.

**`models/latest/` is empty:** A previous training run may have failed mid-write. Delete `models/latest/` and re-run `uv run python -m training.pipeline`.

---

## Approximate Demo Time

| Step | Time |
|---|---|
| Show feature matrix | 30 seconds |
| Run tests | 60 seconds |
| Run training pipeline | 15 seconds |
| Show model card | 60 seconds |
| Show evaluation report | 30 seconds |
| Show registry | 30 seconds |
| Load model and predict | 30 seconds |
| Explain architecture | 90 seconds |
| **Total** | **~5 minutes** |
