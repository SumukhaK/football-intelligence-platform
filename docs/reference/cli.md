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

Expected: `426 passed` (no integration tests selected).

---

## SHAP Explainability

### `python -m explainability.pipeline`

Loads the trained model and feature matrix, computes SHAP values for all matches, and persists JSON artifacts and visualisation plots.

**Usage:**
```sh
uv run python -m explainability.pipeline [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--model-path PATH` | `models/latest/model.joblib` | Path to the trained model bundle. |
| `--feature-matrix PATH` | `datasets/features/feature_matrix.parquet` | Path to the feature matrix. |
| `--output-dir DIR` | `explanations/` | Directory to write all artifacts. |
| `--n-local N` | `10` | Number of per-sample local explanations to persist. |

**Outputs:**

| File | Description |
|---|---|
| `explanations/global_summary.json` | Mean \|SHAP\| per feature; top features by outcome class |
| `explanations/local_explanations.json` | N per-sample explanations with full feature contributions |
| `explanations/summary_plot.png` | Beeswarm plot — feature impact distribution across all samples |
| `explanations/feature_importance.png` | Mean \|SHAP\| bar chart — global feature ranking |
| `explanations/waterfall/sample_NNNN_<class>.png` | Waterfall plots (N samples × 3 classes) |
| `explanations/force/sample_NNNN_<class>.png` | Force plots (N samples × 3 classes) |
| `explanations/dependence/<feature>.png` | Top-5 feature dependence plots |

**Exit codes:** `0` on success, `1` on any failure.

---

## Backend API

### `uvicorn backend.app.main:app`

Starts the FastAPI backend server.

**Usage:**
```sh
# Development (auto-reload on file changes)
uv run uvicorn backend.app.main:app --reload

# Production
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

**Environment variables:**

| Variable | Default | Description |
|---|---|---|
| `MODEL_PATH` | `models/latest/model.joblib` | Path to the trained model bundle |
| `REGISTRY_PATH` | `models/registry.json` | Path to the model registry |
| `LOG_LEVEL` | `info` | Logging level |
| `API_VERSION` | `0.2.0` | API version string returned in `/health` |

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service health, model loaded status, assistant availability |
| `GET` | `/model` | Latest model version, training metrics, git commit |
| `POST` | `/predict` | Match outcome prediction (H/D/A) with probabilities |
| `POST` | `/explain` | Prediction + full SHAP feature contributions |
| `POST` | `/assistant/chat` | RAG assistant chat (requires Ollama + built index) |
| `GET` | `/docs` | Swagger UI — interactive API documentation |
| `GET` | `/redoc` | ReDoc — alternative API documentation |

**Sample health check:**
```sh
curl http://localhost:8000/health
# {"status":"ok","model_loaded":true,"explanation_service_available":true,"assistant_available":true,"version":"0.2.0"}
```

**Sample prediction:**
```sh
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Arsenal", "away_team": "Chelsea", "features": {}}' \
  | python -m json.tool
```

**Sample explanation:**
```sh
curl -s -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Arsenal", "away_team": "Chelsea", "features": {}}' \
  | python -m json.tool
```

---

## AI Assistant Index

### `python -m assistant.pipeline`

Builds or loads the RAG knowledge index and optionally runs a sample query. Requires Ollama running with `nomic-embed-text` pulled.

**Usage:**
```sh
# Build a fresh index from the knowledge base
uv run python -m assistant.pipeline --rebuild

# Load existing index and run a sample query
uv run python -m assistant.pipeline
```

**Prerequisites:**
```sh
ollama pull nomic-embed-text
ollama pull llama3.2
```

**Environment variables:**

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_CHAT_MODEL` | `llama3.2` | Chat generation model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `ASSISTANT_VECTOR_STORE_PATH` | `assistant/vector_store` | Persisted index path |
| `ASSISTANT_TOP_K` | `5` | Top-K chunks to retrieve per query |

**Outputs:**
- `assistant/vector_store/` — persisted numpy vector store (embeddings + metadata)

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

Run the complete AI pipeline in sequence from `ai/`:

```sh
# Data pipeline
uv run python -m scripts.ingest_football_data && \
uv run python -m feature_engineering.pipeline && \
uv run python -m training.pipeline && \
uv run python -m explainability.pipeline

# Start the backend
uv run uvicorn backend.app.main:app --reload
```

Total expected time: approximately 15–30 seconds on a modern machine (excluding first-run dependency download). Add ~2–5 minutes for the explainability pipeline on the first run (SHAP plot generation).

### With AI Assistant (requires Ollama)

```sh
# Pull Ollama models (one-time)
ollama pull nomic-embed-text
ollama pull llama3.2

# Build the knowledge index
uv run python -m assistant.pipeline --rebuild

# Start the backend (assistant loads automatically)
uv run uvicorn backend.app.main:app --reload
```
