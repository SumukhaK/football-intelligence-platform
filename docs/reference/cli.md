# CLI Reference

Every supported command in the Football Intelligence Platform AI workspace.

All commands are run from the `ai/` directory unless otherwise stated.

---

## Prerequisites

```sh
cd ai
uv sync --extra dev   # install all runtime + dev dependencies
```

---

## Data Ingestion

See [data ingestion commands](cli-data.md#data-ingestion).

## Feature Engineering

See [feature engineering](cli-data.md#feature-engineering).

## Model Training

See [training, evaluation and serving refits](cli-models.md#model-training).

## Quality Checks

These commands verify code correctness and formatting. Run them from `ai/`.

```sh
uv run ruff check .        # Expected: All checks passed!
uv run black --check .     # Expected: N files would be left unchanged. (uv run black . applies formatting)
uv run mypy .              # Expected: Success: no issues found in N source files
```

### Tests

```sh
# All tests, including integration tests
uv run pytest

# Skip integration tests (for example on a clean checkout, or offline)
uv run pytest -m "not integration"

# With coverage report
uv run pytest --cov --cov-report=term-missing

# Run a specific test file
uv run pytest tests/training/test_trainer.py

# Only integration tests (need a trained model; one needs network)
uv run pytest -m integration
```

The v2.6.0 release records 1,373 Python tests, with 37 marked integration. Artifact-dependent integration cases need local model/data files and may skip when absent; one marked test downloads live data. `-m "not integration"` excludes the marked group. Totals are release evidence, not an expected fresh result.

---

## SHAP Explainability

### `python -m explainability.pipeline`

Loads the trained model and feature matrix, computes SHAP values for all matches, and persists JSON artifacts and visualisation plots.

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--model-path PATH` | `models/latest/model.joblib` | Path to the trained model bundle. |
| `--feature-matrix PATH` | `datasets/features/feature_matrix.parquet` | Path to the feature matrix. The served model uses `../datasets/features/top5/feature_matrix.parquet`. |
| `--explanations-dir DIR` | `explanations` | Directory to write all artifacts. |
| `--n-top-features N` | `10` | Number of top features to report. |
| `--n-local-samples N` | `10` | Number of per-sample local explanations to persist. |
| `--n-dependence-plots N` | `5` | Number of feature dependence plots. |

**Example (served model):**
```sh
uv run python -m explainability.pipeline --feature-matrix ../datasets/features/top5/feature_matrix.parquet
```

Prints the model, feature matrix and output paths, then the number of samples, features and local explanations, and the artifacts directory.

**Outputs:**

| File | Description |
|---|---|
| `explanations/global_summary.json` | Mean \|SHAP\| per feature; top features by outcome class |
| `explanations/local_explanations.json` | N per-sample explanations with full feature contributions |
| `explanations/summary_plot.png` | Beeswarm plot — feature impact distribution across all samples |
| `explanations/feature_importance.png` | Mean \|SHAP\| bar chart — global feature ranking |
| `explanations/waterfall/sample_NNNN_<class>.png` | Waterfall plots (N samples × 3 classes) |
| `explanations/force/sample_NNNN_<class>.png` | Force plots (N samples × 3 classes) |
| `explanations/dependence/<feature>.png` | Feature dependence plots (5 by default) |

**Exit codes:** `0` on success, `1` on any failure.

---

## Backend API

See [server configuration and snapshot commands](cli-runtime.md#backend-api).

## AI Assistant Index

See [index builds and assistant evaluations](cli-runtime.md#ai-assistant-index).

## Android Build

See [Android commands](cli-runtime.md#android-build).

## Full Pipeline (End-to-End)

Build and promote a frozen-split five-league reporting model from `ai/`. This replaces `models/latest/`; use `--no-promote` when comparing a candidate. To reproduce the all-season serving refit, continue with the [refit workflow](cli-models.md#serving-refit-adr-017).

```sh
# 1. Download and check the five leagues, 2000/01 to 2025/26
uv run python -m scripts.backfill_football_data --base-dir ../datasets --confirm

# 2. Build the feature matrix (use the file name printed by step 1)
uv run python -m feature_engineering.pipeline --input ../datasets/processed/football_data/match_results_top5_v<ts>.csv --output-dir ../datasets/features/top5

# 3. Train with whole-season splits
uv run python -m training.pipeline --feature-matrix ../datasets/features/top5/feature_matrix.parquet --split-strategy season --val-seasons 2022/23 --test-seasons 2023/24 --holdout-seasons 2024/25 2025/26 --max-depth 3 --learning-rate 0.03 --n-estimators 400

# 4. SHAP explanations
uv run python -m explainability.pipeline --feature-matrix ../datasets/features/top5/feature_matrix.parquet

# Start the backend
uv run uvicorn backend.app.main:app --reload
```

The first backfill downloads every season file, so it takes longer than later runs, which reuse the files already downloaded. Local startup enables daily refresh by default; the snapshot container disables it.

To add the AI assistant, build its index with `uv run python -m assistant.pipeline --rebuild` (see [AI Assistant Index](cli-runtime.md#ai-assistant-index)) and restart the backend.
