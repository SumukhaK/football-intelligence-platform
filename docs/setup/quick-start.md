# Quick Start Guide

Get the Football Intelligence Platform running from a clean checkout. Setup takes about 10 minutes; the first five-league data download and training run take longer.

---

## Overview

The platform has two independent workspaces:

- **AI workspace** (`ai/`) — Python 3.12, managed with uv. Runs the full data-to-model pipeline and the FastAPI backend.
- **Android workspace** (`frontend/`) — Kotlin + Compose Multiplatform, managed with Gradle. Builds the Android app: Fixtures, Predict, Assistant and Settings tabs, with an offline cache.

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
| Android SDK | API 35 (compileSdk and targetSdk); minSdk 26 | Installed via Android Studio SDK Manager |
| Git | 2.40+ | Standard installation |
| Network | Active connection | Required for first-run dependency download, data download and the daily refresh |

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
uv run pytest                # Tests — 872 tests
```

`uv run pytest` runs all 872 tests, including the 37 integration tests. The integration tests need a trained model in `ai/models/latest/` (and one needs network access), so on a clean checkout run `uv run pytest -m "not integration"` (835 tests) until you have trained the model below.

---

## Run the AI Pipeline

The AI pipeline builds the served five-league model in four steps (Steps 1–4). Steps 5 and 6 start the backend and, optionally, the assistant. All commands are executed from the `ai/` directory.

### Step 1 — Download the Five Leagues

Downloads the Premier League, Bundesliga, La Liga, Serie A and Ligue 1 from football-data.co.uk, 2000/01 to 2025/26, checks every season, and writes one combined dataset.

```sh
uv run python -m scripts.backfill_football_data --base-dir ../datasets --confirm
```

The script prints the plan (divisions, seasons, files to download), then the row count and the paths of the processed CSV and its report:

```
datasets/processed/football_data/match_results_top5_v<timestamp>.csv
datasets/processed/football_data/match_results_top5_v<timestamp>_report.json
```

Without `--confirm` it only prints the plan. Season files already downloaded are reused, so a second run is quick.

The backend reads its match history from the same folder (`MATCHES_DIR=../datasets/processed/football_data`), so this step also gives the server the data it needs to compute features for predictions.

> **Legacy single-season option:** `uv run python -m scripts.ingest_football_data --base-dir ../datasets` downloads one season of one league (default Premier League 2023/24). This was the original v0.1 pipeline. It is kept for reference and is not used by the served model.

### Step 2 — Feature Engineering

Loads the canonical dataset and builds the feature matrix with 42 pre-match model features.

```sh
uv run python -m feature_engineering.pipeline --input ../datasets/processed/football_data/match_results_top5_v<timestamp>.csv --output-dir ../datasets/features/top5
```

Replace `<timestamp>` with the file name from Step 1. The pipeline prints the input and output paths, then:

```
Pipeline complete in <seconds>s
Rows: <N> in -> <N> out
Feature columns: 67
Validation: PASSED

Outputs written to: ../datasets/features/top5
```

`Feature columns: 67` counts every column in the matrix; 42 of them are model features.

### Step 3 — Train Model

Trains the XGBoost classifier with whole-season splits (ADR 007), evaluates it, and writes artifacts to `ai/models/`.

```sh
uv run python -m training.pipeline --feature-matrix ../datasets/features/top5/feature_matrix.parquet --split-strategy season --val-seasons 2022/23 --test-seasons 2023/24 --holdout-seasons 2024/25 2025/26 --max-depth 3 --learning-rate 0.03 --n-estimators 400
```

The pipeline prints the version, best iteration, features used, test accuracy, F1 and log loss, the run directory, and a final `Promoted:` line (`yes` unless you pass `--no-promote`). A promoted run replaces `models/latest/`.

For reference, the frozen-split model this command produced (version `20260928_123224`) reached test accuracy 0.5245 and log loss 0.9762 on 2023/24, with best iteration 167. See `ai/models/latest/model_card.md` after training.

The live API serves a refit of that model on every season through 2025/26 (`20261007_154105`, 168 trees, ADR 017). To build and serve one, see `training.refit` and `training.promote_refit` in the [root README](../../README.md#running-the-ai-pipeline).

### Step 4 — Generate SHAP Explanations

Computes SHAP values for every match in the feature matrix and writes JSON artifacts and plots to `ai/explanations/`.

```sh
uv run python -m explainability.pipeline --feature-matrix ../datasets/features/top5/feature_matrix.parquet
```

The pipeline prints the model, feature matrix and output paths, then the number of samples, features (42) and local explanations (10 by default).

### Step 5 — Start the Backend

Starts the FastAPI server exposing predictions, explanations, fixtures, insights and (optionally) the AI assistant.

```sh
cp .env.example .env   # optional: every value in it is already the default
uv run uvicorn backend.app.main:app --reload
```

Among the startup log lines you should see:

```
Starting Football Intelligence backend v2.0.0
Match history loaded: Premier League <season>, <N> teams      (one line per league)
Goals models fitted: ...
Fixtures loaded, downloaded at ...
Daily data refresh at 06:00; refreshing now: <True/False>
Prediction model loaded: version=<timestamp> path=...
Explanation service loaded: version=<timestamp>
Assistant service not loaded: ...                              (until Step 6)
Application startup complete.
```

The server also loads the original v1 Premier League model (`V1_MODEL_PATH`) for the `/v1` paths; if that file is missing it logs `Model not found at ...` and only the v1 endpoints are disabled. Every day at 06:00 local time the server downloads the latest results and fixtures. Set `LIVE_REFRESH_HOUR=off` in `.env` to work offline.

Verify it is running:

```sh
curl http://localhost:8000/v2/health
# {"status":"ok","model_loaded":true,"explainability_available":true,"assistant_available":false,
#  "fixture_features_available":true,"insights_available":true,"matches_through":"<date>",
#  "last_refresh_at":<time or null>,"last_refresh_error":null,"version":"2.0.0"}
```

Try a prediction. Only the team names are needed; the server computes the features from match history (ADR 008):

```sh
curl -X POST http://localhost:8000/v2/predict -H "Content-Type: application/json" -d '{"home_team": "Arsenal", "away_team": "Man City", "competition": "Premier League"}'
```

Interactive API docs are at `http://localhost:8000/docs`. The full contract is in [`docs/api.md`](../api.md).

### Step 6 — Build the AI Assistant Index (optional — requires Ollama)

The assistant requires [Ollama](https://ollama.com) running locally with two models pulled.

```sh
# Pull models (one-time, ~5 GB)
ollama pull nomic-embed-text
ollama pull qwen2.5:7b-instruct

# Build the knowledge index
uv run python -m assistant.pipeline --rebuild
```

It prints `Index built: <N> chunks in assistant/vector_store`. Restart the backend after building the index — it will detect the index and enable `/v2/assistant/chat`.

---

## Build Android

Requires JDK 17+ on your `PATH`.

```sh
# From the repository root
cd frontend

# Build debug APK
./gradlew assembleDebug        # macOS/Linux
.\gradlew.bat assembleDebug    # Windows PowerShell

# Run all frontend checks
./gradlew detekt testDebugUnitTest assembleDebug spotlessCheck
```

The debug APK is written to `frontend/app/build/outputs/apk/debug/app-debug.apk`.

The app calls the backend at `http://10.0.2.2:8000/v2`, which is the Android emulator's address for your computer. Start the backend (Step 5) before opening the app. If the backend is not reachable, the app shows saved data with an offline banner; pull down to refresh.

> The first run downloads all Gradle and Kotlin dependencies (~500 MB). Subsequent runs use the Gradle cache and complete in seconds.

---

## Expected Artifacts

After running the complete pipeline, the following files should exist. Paths are from the repository root.

| Path | Description |
|---|---|
| `datasets/raw/football_data/match_results/<DIV>_<season>.csv` | One raw file per league season from football-data.co.uk |
| `datasets/processed/football_data/match_results_top5_v<ts>.csv` | Canonical ProcessedMatch CSV, all five leagues |
| `datasets/processed/football_data/match_results_top5_v<ts>_report.json` | Per-season checks, checksums and row counts |
| `datasets/processed/football_data/match_results_live_v<ts>.csv` | Adds the season in progress (written by the daily refresh) |
| `datasets/processed/openfootball/fixtures_v<ts>.csv` | Upcoming fixtures (written by the daily refresh) |
| `datasets/features/top5/feature_matrix.parquet` | Feature matrix with 42 model features (Parquet) |
| `datasets/features/top5/feature_metadata.json` | Feature metadata |
| `datasets/features/top5/feature_generation_report.json` | Generation report with timing and row counts |
| `ai/models/latest/model.joblib` | Trained XGBoost model (joblib bundle) |
| `ai/models/latest/model_card.md` | Auto-generated model card |
| `ai/models/latest/evaluation_report.json` | Full evaluation report (metrics + CV) |
| `ai/models/latest/config.json` | Training configuration |
| `ai/models/runs/<ts>/` | Every training run, promoted or not |
| `ai/models/registry.json` | Local model registry |
| `ai/models/evaluation/evaluation_report.json` | Global evaluation report |
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

### `FAILED: ...` when downloading data

The download scripts need internet access. `scripts.backfill_football_data` prints `FAILED: <reason>` and exits with code 1; the legacy `scripts.ingest_football_data` prints `Downloading... FAILED` followed by `Error: <reason>`. Check your network connection and retry. The files come from `https://www.football-data.co.uk/mmz4281/<season>/<division>.csv`, for example `.../2324/E0.csv`.

### `ERROR: No canonical CSV found matching ...`

`feature_engineering.pipeline` was run without `--input`. Its default only looks for single-season files under `ai/datasets/`. Pass `--input` with the `match_results_top5_v<ts>.csv` file from Step 1.

### `ERROR: [Errno 2] No such file or directory: ...feature_matrix.parquet`

Training or explainability could not find the feature matrix. Run Steps 1 and 2 first, and pass `--feature-matrix ../datasets/features/top5/feature_matrix.parquet`.

### Android: `SDK location not found`

Create `frontend/local.properties` with your Android SDK path:
```
sdk.dir=/Users/<you>/Library/Android/sdk       # macOS
sdk.dir=C\:\\Users\\<you>\\AppData\\Local\\Android\\Sdk  # Windows
```

### Android: `Unsupported class file major version`

Your JDK version is too old. Install JDK 17 or higher.

### `pytest` failures on a clean checkout

Run `uv sync --extra dev` first to ensure all dev dependencies are installed. If only integration tests fail, train the model first or run `uv run pytest -m "not integration"`.

More fixes are in the [troubleshooting guide](../troubleshooting.md).

---

## Verification Checklist

After setup, verify the following:

- [ ] `uv run ruff check .` — prints `All checks passed!`
- [ ] `uv run black --check .` — prints `N files would be left unchanged.`
- [ ] `uv run mypy .` — prints `Success: no issues found`
- [ ] `uv run pytest` — all 872 tests pass (after training)
- [ ] The backfill produces `datasets/processed/football_data/match_results_top5_v<ts>.csv`
- [ ] Feature engineering produces `datasets/features/top5/feature_matrix.parquet`
- [ ] Training produces `ai/models/latest/model.joblib` and `ai/models/latest/model_card.md`
- [ ] SHAP pipeline produces `ai/explanations/global_summary.json` and plots
- [ ] `curl http://localhost:8000/v2/health` returns `{"status":"ok","model_loaded":true,...}`
- [ ] `POST /v2/predict` returns a predicted result with probabilities
- [ ] `POST /v2/explain` returns SHAP feature contributions
- [ ] Android build prints `BUILD SUCCESSFUL`
