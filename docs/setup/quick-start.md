# Quick Start Guide

Get the Football Intelligence Platform running from a clean checkout in under 10 minutes.

---

## Overview

The platform has two independent workspaces:

- **AI workspace** (`ai/`) — Python 3.12, managed with uv. Runs the full data-to-model pipeline.
- **Android workspace** (`frontend/`) — Kotlin + Compose Multiplatform, managed with Gradle. Builds the Android application shell.

Both workspaces are self-contained. You can set up either or both depending on what you want to do.

---

## System Requirements

| Requirement | Minimum | Notes |
|---|---|---|
| Operating system | Windows 10, macOS 12, Ubuntu 22.04 | All three are supported |
| Python | 3.12.x | Enforced by `pyproject.toml` |
| [uv](https://docs.astral.sh/uv/) | 0.4.0+ | Replaces pip + venv; install once globally |
| JDK | 17+ | Required for Android build only |
| Android Studio | Ladybug (2024.2.1) or newer | Required for Android development |
| Android SDK | API 34 (compileSdk) | Installed via Android Studio SDK Manager |
| Git | 2.40+ | Standard installation |
| Network | Active connection | Required for first-run dependency download and data ingestion |

> **Windows users:** All commands below are written for PowerShell. If you are using Git Bash or WSL, substitute `/` for `\` in paths.

---

## Clone Repository

```sh
git clone https://github.com/SumukhaK/football-intelligence-platform.git
cd football-intelligence-platform
```

---

## Install AI Dependencies

All Python dependency management happens through uv inside the `ai/` directory.

```sh
cd ai
uv sync --extra dev
```

This creates a `.venv` inside `ai/` and installs all runtime and development dependencies. You do not need to activate the virtual environment manually — all `uv run` commands activate it automatically.

Verify the installation:

```sh
uv run python --version
# Python 3.12.x
```

---

## Run the Quality Checks (AI)

Confirm the AI workspace is clean before running any pipelines:

```sh
# From ai/
uv run ruff check .          # Linting — should print: All checks passed!
uv run black --check .       # Formatting — should print: N files would be left unchanged.
uv run mypy .                # Type checking — should print: Success: no issues found in N source files
uv run pytest                # Tests — should print: 266 passed
```

All four checks must pass on a clean checkout.

---

## Run the AI Pipeline

The AI pipeline runs in three sequential steps. All commands are executed from the `ai/` directory.

### Step 1 — Ingest Data

Downloads the Premier League 2023/24 dataset from football-data.co.uk and saves it to `datasets/raw/`.

```sh
uv run python -m scripts.ingest_football_data
```

Expected output:

```
Football Intelligence Platform — Data Ingestion
================================================
Provider:    football-data.co.uk
Competition: Premier League
Season:      2023/24
Output dir:  datasets

Downloading... Done (1.9s)

Rows ingested:  380

Raw dataset:    datasets/raw/football_data/match_results_v<timestamp>.csv
Processed:      datasets/processed/football_data/match_results_v<timestamp>.csv
Metadata:       datasets/raw/football_data/match_results_v<timestamp>_metadata.json
Version:        <timestamp>
Checksum:       <sha256>
```

> Requires an active internet connection. The download is approximately 30 KB.

### Step 2 — Feature Engineering

Loads the canonical dataset and produces a 42-column feature matrix saved to `datasets/features/`.

```sh
uv run python -m feature_engineering.pipeline
```

Expected output:

```
Input:      datasets/processed/football_data/match_results_v<timestamp>.csv
Output dir: datasets/features

Pipeline complete in 1.8s
Rows: 380 in -> 380 out
Feature columns: 67
Validation: PASSED

Outputs written to: datasets/features
```

### Step 3 — Train Model

Trains the XGBoost classifier, evaluates it, and writes artifacts to `models/`.

```sh
uv run python -m training.pipeline
```

Expected output:

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

### Step 4 — Generate SHAP Explanations

Computes SHAP values for all 380 matches and writes JSON artifacts and visualisation plots.

```sh
uv run python -m explainability.pipeline
```

Expected output:

```
Model:          .../models/latest/model.joblib
Feature matrix: .../datasets/features/feature_matrix.parquet
Output:         .../explanations

Samples:        380
Features:       42
Local explanations: 10
Artifacts:      .../explanations
```

### Step 5 — Start the Backend

Starts the FastAPI server exposing predictions, explanations, and (optionally) the AI assistant.

```sh
uv run uvicorn backend.app.main:app --reload
```

Expected log output:

```
INFO: Prediction model loaded: version=<timestamp>
INFO: Explanation service loaded.
INFO: Application startup complete.
```

Verify it is running:

```sh
curl http://localhost:8000/health
# {"status":"ok","model_loaded":true,"explanation_service_available":true,"assistant_available":false,"version":"0.2.0"}
```

### Step 6 — Build the AI Assistant Index (optional — requires Ollama)

The assistant requires [Ollama](https://ollama.com) running locally with two models pulled.

```sh
# Pull models (one-time, ~4 GB)
ollama pull nomic-embed-text
ollama pull llama3.2

# Build the knowledge index
uv run python -m assistant.pipeline --rebuild
```

Restart the backend after building the index — it will detect the index and enable the assistant endpoint.

---

## Build Android

Requires JDK 17+ on your `PATH`.

```sh
# From the repository root
cd frontend

# Build debug APK
./gradlew assembleDebug        # macOS/Linux
.\gradlew.bat assembleDebug    # Windows PowerShell

# Run unit tests
./gradlew testDebugUnitTest
```

The debug APK is written to `frontend/app/build/outputs/apk/debug/app-debug.apk`.

> The first run downloads all Gradle and Kotlin dependencies (~500 MB). Subsequent runs use the Gradle cache and complete in seconds.

---

## Expected Artifacts

After running the complete pipeline, the following files should exist:

| Path | Description |
|---|---|
| `datasets/raw/football_data/match_results_v<ts>.csv` | Raw match data from football-data.co.uk |
| `datasets/processed/football_data/match_results_v<ts>.csv` | Canonical ProcessedMatch CSV |
| `datasets/features/feature_matrix.parquet` | 42-column feature matrix (Parquet) |
| `datasets/features/feature_metadata.json` | Feature metadata and generation report |
| `models/latest/model.joblib` | Trained XGBoost model (joblib bundle) |
| `models/latest/model_card.md` | Auto-generated model card |
| `models/latest/evaluation_report.json` | Full evaluation report (metrics + CV) |
| `models/latest/config.json` | Training configuration |
| `models/registry.json` | Local model registry |
| `models/evaluation/evaluation_report.json` | Global evaluation report |
| `ai/explanations/global_summary.json` | Mean \|SHAP\| per feature across all matches |
| `ai/explanations/local_explanations.json` | 10 per-sample SHAP explanations |
| `ai/explanations/summary_plot.png` | Beeswarm feature impact plot |
| `ai/explanations/feature_importance.png` | Mean \|SHAP\| bar chart |
| `ai/assistant/vector_store/` | Persisted RAG knowledge index (if built) |

---

## Common Errors

### `uv: command not found`

Install uv:
```sh
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### `Python 3.12 not found`

uv can install Python automatically:
```sh
uv python install 3.12
```

### `ERROR: Failed to download dataset`

The ingestion pipeline requires internet access. Check your network connection and retry. The target URL is `https://www.football-data.co.uk/mmz4281/2324/E0.csv`.

### `FileNotFoundError: feature_matrix.parquet not found`

You must run the ingestion and feature engineering steps before training. Run them in order: ingest → feature engineering → train.

### Android: `SDK location not found`

Create `frontend/local.properties` with your Android SDK path:
```
sdk.dir=/Users/<you>/Library/Android/sdk       # macOS
sdk.dir=C\:\\Users\\<you>\\AppData\\Local\\Android\\Sdk  # Windows
```

### Android: `Unsupported class file major version`

Your JDK version is too old. Install JDK 17 or higher.

### `pytest` failures on a clean checkout

Run `uv sync --extra dev` first to ensure all dev dependencies are installed.

---

## Verification Checklist

After setup, verify the following:

- [ ] `uv run ruff check .` — prints `All checks passed!`
- [ ] `uv run black --check .` — prints `N files would be left unchanged.`
- [ ] `uv run mypy .` — prints `Success: no issues found`
- [ ] `uv run pytest` — prints `426 passed`
- [ ] Data ingestion produces a `datasets/raw/` CSV
- [ ] Feature engineering produces `datasets/features/feature_matrix.parquet`
- [ ] Training produces `models/latest/model.joblib` and `models/latest/model_card.md`
- [ ] SHAP pipeline produces `ai/explanations/global_summary.json` and plots
- [ ] `curl http://localhost:8000/health` returns `{"status":"ok","model_loaded":true,...}`
- [ ] `POST /predict` returns a predicted result with probabilities
- [ ] `POST /explain` returns SHAP feature contributions
- [ ] Android build prints `BUILD SUCCESSFUL`
