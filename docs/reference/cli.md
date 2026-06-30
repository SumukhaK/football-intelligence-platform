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

### `python -m scripts.ingest_football_data`

Downloads match data from football-data.co.uk, validates it against the `ProcessedMatch` schema, and writes three output files.

**Usage:**
```sh
uv run python -m scripts.ingest_football_data [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--season SEASON` | `2324` | Four-digit season code. `2324` = 2023/24 season. |
| `--division DIV` | `E0` | Division code. `E0` = Premier League. `E1` = Championship. |
| `--base-dir DIR` | `datasets/` | Override the datasets base directory. |

**Examples:**
```sh
# Default: Premier League 2023/24
uv run python -m scripts.ingest_football_data

# Specify season and division explicitly
uv run python -m scripts.ingest_football_data --season 2324 --division E0

# Write to a custom directory
uv run python -m scripts.ingest_football_data --base-dir /tmp/datasets
```

**Inputs:** Network access to `https://www.football-data.co.uk/mmz4281/<season>/<division>.csv`.

**Outputs:**

| File | Location | Description |
|---|---|---|
| Raw CSV | `datasets/raw/football_data/match_results_v<ts>.csv` | Immutable raw source data |
| Processed CSV | `datasets/processed/football_data/match_results_v<ts>.csv` | Canonical `ProcessedMatch` schema |
| Metadata JSON | `datasets/raw/football_data/match_results_v<ts>_metadata.json` | Provenance, checksum, version |

**Exit codes:** `0` on success, `1` on any failure (network error, validation failure, IO error).

**Sample output:**
```
Football Intelligence Platform — Data Ingestion
================================================
Provider:    football-data.co.uk
Competition: Premier League
Season:      2023/24
Output dir:  datasets

Downloading... Done (1.9s)

Rows ingested:  380

Raw dataset:    datasets/raw/football_data/match_results_v20260630_090657.csv
Processed:      datasets/processed/football_data/match_results_v20260630_090657.csv
Metadata:       datasets/raw/football_data/match_results_v20260630_090657_metadata.json
Version:        20260630_090657
Checksum:       b2e057b0...
```

---

## Feature Engineering

### `python -m feature_engineering.pipeline`

Loads the latest canonical `ProcessedMatch` CSV, executes 9 feature generators in dependency order, validates the output, and writes a Parquet feature matrix.

**Usage:**
```sh
uv run python -m feature_engineering.pipeline [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--input PATH` | auto-detect latest | Path to a specific `ProcessedMatch` CSV. Defaults to the most recently modified file in `datasets/processed/`. |
| `--output-dir DIR` | `datasets/features` | Directory to write output artifacts. |

**Examples:**
```sh
# Default: uses the latest processed CSV
uv run python -m feature_engineering.pipeline

# Specify input and output explicitly
uv run python -m feature_engineering.pipeline \
  --input datasets/processed/football_data/match_results_v20260630_090657.csv \
  --output-dir datasets/features
```

**Inputs:** The canonical `ProcessedMatch` CSV produced by the ingestion pipeline.

**Outputs:**

| File | Location | Description |
|---|---|---|
| Feature matrix | `datasets/features/feature_matrix.parquet` | 42 pre-match engineered features (Parquet) |
| Feature metadata | `datasets/features/feature_metadata.json` | Per-feature descriptions and generation report |
| Generation report | `datasets/features/feature_generation_report.json` | Pipeline execution report with timing and row counts |

**Exit codes:** `0` on success and validation passing, `1` on any error or validation failure.

**Feature generators (in execution order):**

| Generator | Features produced |
|---|---|
| `GoalStatisticsFeature` | Goals scored, conceded, difference (last 5/10 matches) |
| `HomeAdvantageFeature` | Expanding home win/draw/loss rates |
| `AwayFormFeature` | Expanding away win/draw/loss rates |
| `RollingFormFeature` | Rolling points, wins (last 5 and 10 matches) |
| `RestDaysFeature` | Days since last match for each team |
| `HeadToHeadFeature` | Historical head-to-head record between teams |
| `LeaguePositionFeature` | League position, points, matches played at kick-off |
| `EloRatingFeature` | Elo ratings (K=32, starting at 1500) |
| `StrengthOfScheduleFeature` | Rolling mean opponent Elo (requires Elo columns) |

**Sample output:**
```
Input:      datasets/processed/football_data/match_results_v20260630_090657.csv
Output dir: datasets/features

Pipeline complete in 1.8s
Rows: 380 in -> 380 out
Feature columns: 67
Validation: PASSED

Outputs written to: datasets/features
```

---

## Model Training

### `python -m training.pipeline`

Loads the feature matrix, performs a chronological 70/15/15 split, trains an XGBoost classifier with early stopping, runs cross-validation, evaluates on all splits, generates a model card, and registers the run.

**Usage:**
```sh
uv run python -m training.pipeline [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--feature-matrix PATH` | `datasets/features/feature_matrix.parquet` | Path to the feature matrix Parquet file. |
| `--models-dir DIR` | `models` | Root directory for model artifacts. |
| `--n-estimators N` | `300` | Maximum number of XGBoost trees. |
| `--learning-rate LR` | `0.1` | XGBoost learning rate (eta). |
| `--max-depth DEPTH` | `6` | Maximum tree depth. |
| `--seed SEED` | `42` | Random seed for reproducibility. |

**Examples:**
```sh
# Default configuration
uv run python -m training.pipeline

# Custom hyperparameters
uv run python -m training.pipeline \
  --n-estimators 500 \
  --learning-rate 0.05 \
  --max-depth 4

# Custom input and output paths
uv run python -m training.pipeline \
  --feature-matrix datasets/features/feature_matrix.parquet \
  --models-dir models
```

**Inputs:** `datasets/features/feature_matrix.parquet` (produced by the feature engineering pipeline).

**Outputs:**

| File | Location | Description |
|---|---|---|
| Model bundle | `models/runs/<ts>/model.joblib` | XGBClassifier + imputer + label encoder |
| Config | `models/runs/<ts>/config.json` | Training hyperparameters |
| Metrics | `models/runs/<ts>/metrics.json` | Per-split metrics (accuracy, F1, log loss, ROC AUC) |
| Evaluation report | `models/runs/<ts>/evaluation_report.json` | Full report including CV results |
| Model card | `models/runs/<ts>/model_card.md` | Human-readable model documentation |
| Feature importance | `models/runs/<ts>/plots/feature_importance.png` | Top-N feature importance bar chart |
| Confusion matrix | `models/runs/<ts>/plots/confusion_matrix.png` | Test set confusion matrix |
| Latest symlink | `models/latest/` | Copy of all artifacts from the most recent run |
| Global eval report | `models/evaluation/evaluation_report.json` | Updated on every run |
| Registry | `models/registry.json` | Appended with a new `ModelEntry` |

**Exit codes:** `0` on success, `1` on any failure.

**Sample output:**
```
Feature matrix: .../datasets/features/feature_matrix.parquet
Models dir:     .../models
Estimators:     300  |  LR: 0.1  |  Depth: 6

Version:        20260630_115224
Best iteration: 10
Features used:  42
Test accuracy:  0.5614
Test F1:        0.5181
Test log-loss:  0.9493
Run dir:        models/runs/20260630_115224
```

---

## Quality Checks

These commands verify code correctness and formatting. Run them from `ai/`.

### Linting

```sh
uv run ruff check .
```

Expected: `All checks passed!`

### Formatting

```sh
uv run black --check .     # check only
uv run black .             # apply formatting
```

Expected (check): `N files would be left unchanged.`

### Type Checking

```sh
uv run mypy .
```

Expected: `Success: no issues found in N source files`

### Tests

```sh
# All tests (excludes integration tests by default)
uv run pytest

# With coverage report
uv run pytest --cov --cov-report=term-missing

# Run a specific test file
uv run pytest tests/training/test_trainer.py

# Run integration tests (requires network)
uv run pytest -m integration
```

Expected: `266 passed` (no integration tests selected).

---

## Android Build

Run from the `frontend/` directory.

```sh
# Build debug APK
./gradlew assembleDebug         # macOS/Linux
.\gradlew.bat assembleDebug     # Windows PowerShell

# Run unit tests
./gradlew testDebugUnitTest

# Static analysis
./gradlew detekt
./gradlew spotlessCheck

# Fix formatting
./gradlew spotlessApply
```

---

## Full Pipeline (End-to-End)

Run all three AI pipeline steps in sequence from `ai/`:

```sh
uv run python -m scripts.ingest_football_data && \
uv run python -m feature_engineering.pipeline && \
uv run python -m training.pipeline
```

Total expected time: approximately 5–10 seconds on a modern machine (excluding first-run dependency download).
