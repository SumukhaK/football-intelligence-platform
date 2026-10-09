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

### `python -m scripts.refresh_live_dataset`

Appends the played matches of the season in progress to the newest completed-season dataset and writes `processed/football_data/match_results_live_v<timestamp>.csv`, which the backend loads at startup (ADR 008). Dry run unless `--confirm` is given.

```sh
uv run python -m scripts.refresh_live_dataset --confirm
```

| Flag | Default | Description |
|---|---|---|
| `--season CODE` | the season today falls in | Season in progress, e.g. `2627`. |
| `--divisions DIV ...` | `E0 D1 SP1 I1 F1` | Leagues to include. |
| `--base-dir DIR` | `../datasets` | Datasets base directory. |
| `--confirm` | off | Download and write. |

Raw snapshots are stored once per division per day under `raw/football_data/match_results_in_progress/`. On success it prints the matches played so far, the last match date and the written path; on failure it prints `FAILED: <reason>` and exits with code 1. Restart the backend afterwards.

The backend runs the same refresh itself every day at `LIVE_REFRESH_HOUR` (default 6; `off` turns it off), so you only need this command when the daily refresh is off or has failed (ADR 013).

---

### `python -m scripts.refresh_fixtures`

Downloads the five leagues' upcoming fixtures from openfootball and writes `processed/openfootball/fixtures_v<timestamp>.csv`, which `/v2/fixtures` serves (ADR 015). Dry run unless `--confirm` is given.

```sh
uv run python -m scripts.refresh_fixtures --confirm
```

| Flag | Default | Description |
|---|---|---|
| `--base-dir DIR` | `../datasets` | Datasets base directory. |
| `--confirm` | off | Download and write. |

Prints the number of upcoming fixtures per league and the written path, or `FAILED: <reason>` with exit code 1. The daily refresh also updates fixtures. Restart the backend afterwards.

---

### `python -m scripts.build_team_crests`

Rebuilds `datasets/schemas/team_crests.csv` and `league_emblems.csv`, the crest URL per team and league that the crest redirects serve (ADR 020). Takes no options.

```sh
uv run python -m scripts.build_team_crests
```

Reads the newest `match_results_top5_v*.csv`, the newest fixtures file and the football-data.org snapshot at `../datasets/raw/kaggle/adrianjuliusaluoch_live_results/football_matches.parquet`. Teams are matched by the games they played, from 2022/23 on, not by spelling. Prints the number of crests and emblems written and the teams left without a crest; the app shows a placeholder for those.

---

### `python -m scripts.backfill_football_data`

Backfills many seasons for the top five leagues (ADR 005), checks every season's integrity (ADR 006), and writes one combined dataset. Runs as a dry run unless `--confirm` is given.

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--divisions DIV ...` | `E0 D1 SP1 I1 F1` | Division codes to include. |
| `--first-season CODE` | `0001` | First season code, `0001` = 2000/01. |
| `--last-season CODE` | `2526` | Last season code, inclusive. |
| `--base-dir DIR` | `datasets/` (relative to `ai/`) | Override the datasets base directory. Pass `../datasets` to use the repository's `datasets/` folder, which the backend reads. |
| `--confirm` | off | Download missing files and build the dataset. Without it, only the plan is printed. |

**Examples:**
```sh
# See what would be downloaded
uv run python -m scripts.backfill_football_data --base-dir ../datasets

# Download and build all five leagues, 2000/01 to 2025/26
uv run python -m scripts.backfill_football_data --base-dir ../datasets --confirm
```

**Behaviour:**
- Season files already in `raw/football_data/match_results/` are reused, never re-downloaded or overwritten.
- Every season must pass the integrity checks: expected team count, each fixture played once, result consistent with goals, dates inside the season window. Ligue 1 2019/20 is whitelisted at 279 matches.
- More than 0.5% unparseable rows in any season fails the run.

**Outputs:**

| File | Location | Description |
|---|---|---|
| Raw CSVs | `datasets/raw/football_data/match_results/<DIV>_<season>.csv` | One immutable file per division season |
| Processed CSV | `datasets/processed/football_data/match_results_top5_v<ts>.csv` | All seasons, canonical `ProcessedMatch` schema, sorted by date |
| Report JSON | `datasets/processed/football_data/match_results_top5_v<ts>_report.json` | Per-season URL, checksum, row counts, errors and warnings. Written even when checks fail |

**Exit codes:** `0` on success or dry run, `1` on any failure. A failure prints `FAILED: <reason>`.

This is the first step of the served model's pipeline. See [Full Pipeline](#full-pipeline-end-to-end).

---

### `python -m scripts.ingest_football_data` (legacy, single season)

The original v0.1 ingestion: downloads one season of one league from football-data.co.uk, validates it against the `ProcessedMatch` schema, and writes a raw CSV, a processed CSV and a metadata JSON (`match_results_v<ts>`) under `raw/football_data/` and `processed/football_data/`. The served model does not use it; use `scripts.backfill_football_data` for the five-league dataset.

```sh
# Default: Premier League 2023/24
uv run python -m scripts.ingest_football_data --base-dir ../datasets

# Specify season and division explicitly
uv run python -m scripts.ingest_football_data --season 2324 --division E0
```

| Flag | Default | Description |
|---|---|---|
| `--season SEASON` | `2324` | Four-digit season code. `2324` = 2023/24 season. |
| `--division DIV` | `E0` | Division code. `E0` = Premier League. `E1` = Championship. |
| `--base-dir DIR` | `datasets/` (relative to `ai/`) | Override the datasets base directory. |

**Output:** a header (provider, competition, season, output dir), then `Downloading... Done (<seconds>s)`, the rows ingested (and `Rows skipped: N` if any rows failed normalisation), and the output paths with the dataset version and checksum. A Premier League season has 380 matches.

**Exit codes:** `0` on success, `1` on any failure (network error, validation failure, IO error). A download failure prints `Downloading... FAILED` followed by `Error: <reason>`.

---

## Feature Engineering

### `python -m feature_engineering.pipeline`

Loads the latest canonical `ProcessedMatch` CSV, executes 9 feature generators in dependency order, validates the output, and writes a Parquet feature matrix.

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--input PATH` | auto-detect latest | Path to a specific `ProcessedMatch` CSV. Without it, the pipeline picks the most recently modified `datasets/processed/football_data/match_results_v*.csv` relative to `ai/`, which only matches legacy single-season files. |
| `--output-dir DIR` | `datasets/features` | Directory to write output artifacts. |

**Examples:**
```sh
# Five-league dataset (served model)
uv run python -m feature_engineering.pipeline \
  --input ../datasets/processed/football_data/match_results_top5_v<ts>.csv \
  --output-dir ../datasets/features/top5

# Legacy: latest single-season CSV under ai/datasets/
uv run python -m feature_engineering.pipeline
```

If no input is given and none is found, it prints `ERROR: No canonical CSV found matching '<pattern>' relative to '<dir>'.` and exits with code 1.

**Inputs:** The canonical `ProcessedMatch` CSV produced by `scripts.backfill_football_data` (or the legacy ingestion).

**Outputs:**

| File | Location | Description |
|---|---|---|
| Feature matrix | `<output-dir>/feature_matrix.parquet` | 42 pre-match engineered features (Parquet) |
| Feature metadata | `<output-dir>/feature_metadata.json` | Per-feature descriptions and generation report |
| Generation report | `<output-dir>/feature_generation_report.json` | Pipeline execution report with timing and row counts |

**Exit codes:** `0` on success and validation passing, `1` on any error or validation failure.

**Feature generators:** goal statistics, home advantage, away form, rolling form, rest days, head-to-head, league position, Elo ratings (K=32, starting at 1500) and strength of schedule (rolling opponent Elo), run in dependency order.

**Sample output:**
```
Input:      ../datasets/processed/football_data/match_results_top5_v<ts>.csv
Output dir: ../datasets/features/top5

Pipeline complete in <seconds>s
Rows: <N> in -> <N> out
Feature columns: 67
Validation: PASSED

Outputs written to: ../datasets/features/top5
```

`Feature columns` counts every column in the matrix; 42 of them are model features.

---

## Model Training

### `python -m training.tuning`

Searches XGBoost hyperparameters by season walk-forward CV on training seasons only, so validation, test and holdout seasons stay unseen (ADR 007).

**Usage:**
```sh
uv run python -m training.tuning --feature-matrix ../datasets/features/top5/feature_matrix.parquet   --val-seasons 2022/23 --test-seasons 2023/24 --holdout-seasons 2024/25 2025/26
```

| Flag | Default | Description |
|---|---|---|
| `--max-depths N ...` | `2 3 4` | Tree depths to try. |
| `--learning-rates LR ...` | `0.03 0.05 0.1` | Learning rates to try. |
| `--n-estimators N ...` | `100 200 400` | Tree counts to try. |
| `--cv-folds N` | `5` | Number of final training seasons used as validation folds. |
| `--output PATH` | `models/tuning/tuning_results.json` | Where to write ranked results. |

Prints every setting ranked by mean CV log loss.

---

### `python -m evaluation.in_season_cli`

Scores the served model on every played match of a season in progress. Each match is predicted from features built only from earlier matches; the model is not retrained. Dry run unless `--confirm` is given.

```sh
uv run python -m evaluation.in_season_cli --season 2627 --confirm
```

| Flag | Default | Description |
|---|---|---|
| `--season CODE` | `2627` | Season in progress. |
| `--divisions DIV ...` | `E0 D1 SP1 I1 F1` | Leagues to score. |
| `--history PATH` | newest `match_results_top5_v*.csv` | Completed-season history. |
| `--model PATH` | `models/latest/model.joblib` | Model to score. |
| `--base-dir DIR` | `../datasets` | Datasets base directory. |
| `--output-dir DIR` | `models/backtests/<season>_<date>` | Where outputs go. |
| `--features PATH` | none | Rescore a saved run's `features/feature_matrix.parquet` instead of downloading. |
| `--through DATE` | none | Score only matches up to this date (`YYYY-MM-DD`). |
| `--confirm` | off | Download and score. |

The report scores the model against an Elo-only baseline (logistic regression on the pre-match Elo gap, fitted on earlier seasons), outcome-frequency priors and Bet365 (pre-match odds with the margin removed; a benchmark only). It adds overall 95% bootstrap ranges for accuracy, log loss, RPS and Brier, and paired bootstraps of the model minus Bet365 and minus Elo only.

Raw snapshots are stored once per division per day under `raw/football_data/match_results_in_progress/`. Outputs: `report.md`, `report.json` and `predictions.csv` (one line per match with probabilities, pick and result).

---

### `python -m evaluation.compare_models`

Scores a candidate run against the current model, bookmaker probabilities and training-set outcome frequencies (ADR 007), then applies the promotion rule. Nothing is promoted.

**Usage:**
```sh
uv run python -m evaluation.compare_models --candidate-run models/runs/<version>   [--feature-matrix PATH] [--current-model PATH] [--current-feature-matrix PATH]
```

| Flag | Default | Description |
|---|---|---|
| `--candidate-run DIR` | required | Run directory with `model.joblib` and `config.json` from a season-split run. |
| `--feature-matrix PATH` | `../datasets/features/top5/feature_matrix.parquet` | Feature matrix the candidate was trained on. |
| `--current-model PATH` | `models/latest/model.joblib` | The model currently served. |
| `--current-feature-matrix PATH` | `../datasets/features/feature_matrix.parquet` | Feature matrix the current model was trained on. |

**Outputs:** `comparison.json` and `comparison.md` in the candidate run directory: log loss, RPS, Brier and accuracy per league for the test and holdout seasons, a paired bootstrap of candidate minus current on the current model's own test matches, and the promotion verdict.

---

### `python -m evaluation.goals_evaluation_cli`

Tunes and backtests the goals model (ADR 009) with a rolling-origin backtest: tunes on the validation season, then forecasts the test season, the holdout seasons and the season in progress, refitting before every matchweek. Compares against a plain Poisson baseline, bookmakers' over 2.5 odds and the served XGBoost model.

```sh
uv run python -m evaluation.goals_evaluation_cli
```

| Flag | Default | Description |
|---|---|---|
| `--matches CSV` | newest live dataset in `../datasets/processed/football_data` | Match history. |
| `--model PATH` | `models/latest/model.joblib` | Served XGBoost model to compare with. |
| `--feature-matrix PATH` | `../datasets/features/top5/feature_matrix.parquet` | That model's feature matrix. |
| `--in-season-xgb CSV` | `models/backtests/2627_20260928_model123224/predictions.csv` | In-season XGBoost predictions from `evaluation.in_season_cli`. |
| `--in-season SEASON` | `2026/27` | Season in progress. |
| `--output-dir DIR` | `models/evaluation/goals` | Where outputs go. |

**Outputs:** `goals_evaluation.json` and `goals_forecasts.csv`.

---

### `python -m evaluation.draw_analysis`

Checks how well the model's draw probabilities are calibrated, and what a "pick a draw when it is close to the favourite" rule would cost in accuracy, per season block. Writes JSON and prints `Wrote <path>`.

| Flag | Default | Description |
|---|---|---|
| `--model PATH` | `models/latest/model.joblib` | Model to analyse. |
| `--feature-matrix PATH` | `../datasets/features/top5/feature_matrix.parquet` | That model's feature matrix. |
| `--in-season CSV` | none | `predictions.csv` from `evaluation.in_season_cli`. |
| `--output PATH` | `models/evaluation/draw_analysis.json` | Report path. |

---

### Experiments

Two one-off experiments that retrain with the served model's configuration and compare log loss with a paired bootstrap. Neither takes any options, and neither changes the served model. Both read `../datasets/features/top5/feature_matrix.parquet` and `models/latest/config.json`.

```sh
# Do draw-oriented features help? (docs/reports/draw-handling.md)
uv run python -m scripts.draw_feature_experiment

# Do Champions League rest days, rolling xG or FIFA ratings help? (docs/reports/kaggle-extras.md)
uv run python -m scripts.kaggle_extras_experiment
```

`scripts.kaggle_extras_experiment` also needs the Kaggle source files in `../datasets/raw/kaggle/`. Both print their results to the console.

---

### `python -m training.pipeline`

Loads the feature matrix, splits it, trains an XGBoost classifier with early stopping, runs cross-validation, evaluates on all splits, generates a model card, and registers the run.

The default split is chronological (70/15/15). The served model uses `--split-strategy season`, which assigns whole seasons to each split (ADR 007). See the first example below.

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--feature-matrix PATH` | `datasets/features/feature_matrix.parquet` | Path to the feature matrix Parquet file. |
| `--models-dir DIR` | `models` | Root directory for model artifacts. |
| `--n-estimators N` | `300` | Maximum number of XGBoost trees. |
| `--learning-rate LR` | `0.1` | XGBoost learning rate (eta). |
| `--max-depth DEPTH` | `6` | Maximum tree depth. |
| `--seed SEED` | `42` | Random seed for reproducibility. |
| `--split-strategy {chronological,season}` | `chronological` | `season` assigns whole seasons (ADR 007) and uses season walk-forward CV. The served model uses `season`. |
| `--val-seasons S ...` | — | Validation seasons for `season`, e.g. `2022/23`. Training uses every earlier season. |
| `--test-seasons S ...` | — | Test seasons for `season`. |
| `--holdout-seasons S ...` | — | Seasons never used in training or model selection. |
| `--no-promote` | off | Write only `models/runs/<version>/`; leave `models/latest/`, the global report and the registry untouched. |

**Examples:**
```sh
# The served model's configuration
uv run python -m training.pipeline \
  --feature-matrix ../datasets/features/top5/feature_matrix.parquet \
  --split-strategy season --val-seasons 2022/23 --test-seasons 2023/24 \
  --holdout-seasons 2024/25 2025/26 \
  --max-depth 3 --learning-rate 0.03 --n-estimators 400

# Same, without replacing the served model
uv run python -m training.pipeline   --feature-matrix ../datasets/features/top5/feature_matrix.parquet   --split-strategy season --val-seasons 2022/23 --test-seasons 2023/24   --holdout-seasons 2024/25 2025/26 --no-promote

# Default configuration (chronological split)
uv run python -m training.pipeline

```

**Inputs:** A feature matrix produced by the feature engineering pipeline. The default path, `datasets/features/feature_matrix.parquet`, is relative to `ai/`; the served model uses `../datasets/features/top5/feature_matrix.parquet`.

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
| Latest | `models/latest/` | Copy of all artifacts from the most recent promoted run |
| Global eval report | `models/evaluation/evaluation_report.json` | Updated on every promoted run |
| Registry | `models/registry.json` | Appended with a new `ModelEntry` on every promoted run |

With `--no-promote`, only `models/runs/<ts>/` is written.

**Exit codes:** `0` on success, `1` on any failure (printed as `ERROR: <reason>`).

**Output:** the feature matrix path, models directory and hyperparameters, then:

```
Version:        <timestamp>
Best iteration: <N>
Features used:  42
Test accuracy:  <value>
Test F1:        <value>
Test log-loss:  <value>
Run dir:        <path>/models/runs/<timestamp>
Promoted:       yes
```

`Promoted:` reads `no` when `--no-promote` is given. For reference, the season-split run `20260928_123224` has test accuracy 0.5245, test log loss 0.9762 and best iteration 167 (`models/runs/20260928_123224/model_card.md`). The served model, `20261007_154105`, is a refit of that run (ADR 017; see below).

---

### Serving refit (ADR 017)

Three steps retrain a season-split run on every completed season and serve it. Each prints `ERROR: <reason>` and exits with code 1 on failure.

```sh
# 1. Retrain on all seasons up to --last-season (default 2025/26) with the
#    source run's settings and best tree count. Writes models/runs/<v>/ only.
uv run python -m training.refit --source-run models/runs/20260928_123224

# 2. Score the refit and the source run on the season so far, using the
#    features saved by evaluation.in_season_cli
uv run python -m evaluation.refit_backtest   --rows models/backtests/<in-season run>/features/feature_matrix.parquet   --frozen-run models/runs/20260928_123224 --refit-run models/runs/<v>

# 3. Copy the refit to models/latest/ and register it with its backtest scores
uv run python -m training.promote_refit --run models/runs/<v>   --backtest models/backtests/refit_<v>/report.json
```

`evaluation.refit_backtest` also takes `--season` (default `2026/27`), `--through` (default `2026-09-20`) and `--output-dir`. `training.promote_refit` takes `--models-dir` (default `models`). The refit has no test season, so the registry holds its current-season scores (`accuracy_2026_27`, ...), and test and holdout results stay quoted from the source run.

---

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

Expected: 970 tests pass with `uv run pytest`. 37 of them are integration tests, which need the trained model in `models/latest/`; `-m "not integration"` runs the other 933. Integration tests are not skipped by default.

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

Set them in `ai/.env` (copy `ai/.env.example`). Every value below is the default, so an empty `.env` works. Paths are relative to `ai/`.

| Variable | Default | Description |
|---|---|---|
| `MODEL_PATH` | `../ai/models/latest/model.joblib` | Model served by `/v2` |
| `REGISTRY_PATH` | `../ai/models/registry.json` | Model registry |
| `V1_MODEL_PATH` | `../ai/models/runs/20260630_132617/model.joblib` | Original Premier League model served by `/v1` and the unversioned paths (ADR 014) |
| `V1_MODEL_VERSION` | `20260630_132617` | Registry version of that model |
| `MATCHES_DIR` | `../datasets/processed/football_data` | Match history; the newest live or five-league dataset is loaded (ADR 008) |
| `DATASETS_DIR` | `../datasets` | Root of raw and processed data, used by the daily refresh |
| `FIXTURES_DIR` | `../datasets/processed/openfootball` | Upcoming fixtures (ADR 015) |
| `SERVED_COMPETITIONS` | `["Premier League","Bundesliga","La Liga","Serie A","Ligue 1"]` | JSON list of served leagues (ADR 012) |
| `DEFAULT_COMPETITION` | `Premier League` | League used when a request names none |
| `LIVE_REFRESH_HOUR` | `6` | Local hour (0–23) of the daily refresh; `off` turns it off (ADR 013) |
| `DRAW_POSSIBLE_THRESHOLD` | `0.28` | Draw probability at or above which `draw_possible` is true (ADR 011) |
| `API_VERSION` | `2.0.0` | API version string returned in `/health` |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `text` | `json` writes one JSON object per log line in the telemetry contract's format (ADR 024) |
| `GCP_PROJECT_ID` | unset | Google Cloud project, used for the trace field on JSON log lines |
| `K_REVISION` | unset | Set by Cloud Run; logged as `revision` on JSON log lines |
| `RATE_LIMIT_PER_MINUTE` | `120` | Requests per minute per client before a 429; `off` turns it off (ADR 014) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_CHAT_MODEL` | `qwen2.5:7b-instruct` | Chat generation model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `ASSISTANT_VECTOR_STORE_PATH` | `assistant/vector_store` | Persisted index path |
| `ASSISTANT_KNOWLEDGE_ROOT` | `.` | Root folder of the assistant's knowledge documents |
| `ASSISTANT_TOP_K` | `5` | Top-K chunks to retrieve per query |
| `AUTH_REQUIRED` | `false` | Require invite-only sign-in and consent on every `/v2` data route, and drop `/v1` (ADR 022) |
| `ACCOUNTS_PATH` | `accounts/accounts.json` | Local accounts file (hashes only; gitignored) |
| `TEAM_CRESTS_PATH` | `../datasets/schemas/team_crests.csv` | Team name → crest URL (ADR 020) |
| `LEAGUE_EMBLEMS_PATH` | `../datasets/schemas/league_emblems.csv` | League name → emblem URL (ADR 020) |

**Endpoints:**

`/v2` is the current API (version 2.0.0). `/v1` and the unversioned paths keep the frozen v1.0.0 contract: the original Premier League model and the original response fields. The full contract is in [`docs/api.md`](../api.md).

| Method | Path | Description |
|---|---|---|
| `GET` | `/v2/health` | Service health: model, explainability, assistant, match features and insights availability, latest result date, last refresh |
| `GET` | `/v2/model` | Served model version, training metrics, git commit |
| `GET` | `/v2/competitions` | The five served leagues and how current each one is |
| `GET` | `/v2/teams` | A league's current teams (`?competition=`) |
| `GET` | `/v2/fixtures` | A league's upcoming fixtures |
| `POST` | `/v2/predict` | Match outcome prediction (H/D/A) with probabilities |
| `POST` | `/v2/explain` | Prediction + full SHAP feature contributions |
| `POST` | `/v2/insights` | Likely scores, expected goals and goal markets from the goals model |
| `POST` | `/v2/assistant/chat` | RAG assistant chat (requires Ollama + built index) |
| `GET` | `/v2/teams/{team}/crest` | Redirect to the team's crest image (ADR 020) |
| `GET` | `/v2/competitions/{competition}/emblem` | Redirect to the league's emblem image (ADR 020) |
| `POST` | `/v2/auth/redeem-invite`, `/v2/auth/login`, `/v2/auth/logout` | Invite-only sign-in (ADR 022) |
| `GET` / `POST` | `/v2/me`, `/v2/me/consent` | The signed-in user, and accepting the notice |
| `GET` | `/docs` | Swagger UI — interactive API documentation |
| `GET` | `/redoc` | ReDoc — alternative API documentation |

With `AUTH_REQUIRED=true`, every `/v2` data route needs `Authorization: Bearer <token>`, and `/v1` and the unversioned paths are not mounted. Health, sign-in and the crest redirects stay open.

Each client may make 120 requests a minute (`RATE_LIMIT_PER_MINUTE`). Beyond that the server answers `429` with a `Retry-After` header. Health checks and the docs are never limited.

**Sample health check:**
```sh
curl http://localhost:8000/v2/health
```

The response has `status`, `model_loaded`, `explainability_available`, `assistant_available`, `fixture_features_available`, `insights_available`, `matches_through`, `last_refresh_at`, `last_refresh_error` and `version` (see [`docs/api.md`](../api.md#get-health) for an example).

**Sample prediction:**

Only the team names are needed; the server computes the features from match history (ADR 008). `competition` is optional and defaults to the Premier League. Do not send `"features": {}`: an empty object counts as supplied features and fails with 422.

```sh
curl -s -X POST http://localhost:8000/v2/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Arsenal", "away_team": "Man City", "competition": "Premier League"}' \
  | python -m json.tool
```

`POST /v2/explain` takes the same body and adds SHAP feature contributions. Team names must match `/v2/teams?competition=<league>`.

### `python -m scripts.manage_accounts`

Invites people and bans or unbans accounts in `ACCOUNTS_PATH` (ADR 022).

```sh
uv run python -m scripts.manage_accounts invite --email sam@example.com
uv run python -m scripts.manage_accounts ban --email sam@example.com
uv run python -m scripts.manage_accounts unban --email sam@example.com
```

`invite` prints a one-time code valid for 7 days; send it to the person privately. They redeem it in the app with a password of at least 10 characters. Inviting an existing account again lets them reset their password. `ban` and `unban` print the account's new status, or exit with code 1 when there is no account for the email.

---

## AI Assistant Index

### `python -m assistant.pipeline`

Builds the RAG knowledge index. Requires Ollama running with `nomic-embed-text` pulled.

**Usage:**
```sh
# Build a fresh index from the knowledge base, replacing any existing one
uv run python -m assistant.pipeline --rebuild

# Build the index only if it does not exist yet; otherwise load it
uv run python -m assistant.pipeline
```

Both print `Index built: <N> chunks in <vector store path>`. Without `--rebuild`, an existing index is loaded and its chunk count is printed; nothing is re-embedded.

**Prerequisites:**
```sh
ollama pull nomic-embed-text
ollama pull qwen2.5:7b-instruct
```

**Environment variables:** `assistant.pipeline` reads `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL` and `OLLAMA_EMBED_MODEL` like the backend, plus `VECTOR_STORE_PATH` (default `assistant/vector_store`) and `KNOWLEDGE_BASE_ROOT` (default `.`). The backend names those two `ASSISTANT_VECTOR_STORE_PATH` and `ASSISTANT_KNOWLEDGE_ROOT`; keep them pointing at the same place.

**Outputs:**
- `assistant/vector_store/` — persisted numpy vector store (embeddings + metadata)

The chat model must support tool calling (`qwen2.5:7b-instruct` does; see ADR 019 for why it is the default), because the assistant calls the prediction, explanation and fixtures services (ADR 018).

### `python -m evaluation.assistant_grounding`

Asks the assistant for the model's prediction of upcoming fixtures in every league, calls `/v2/predict` and `/v2/explain` for the same matches, and checks each answer quotes the predicted outcome's probability and contains no number those responses or the question don't account for. One extra question names a team that doesn't exist. Exits non-zero if any case fails.

```sh
LIVE_REFRESH_HOUR=off uv run python -m evaluation.assistant_grounding --per-league 2
```

### `python -m evaluation.assistant_abstention`

Asks 10 questions the knowledge base answers and 10 it doesn't, and checks the assistant answers the first set and replies "I don't have enough information in my knowledge base to answer that." to the second. Exits non-zero if any case fails.

```sh
LIVE_REFRESH_HOUR=off uv run python -m evaluation.assistant_abstention
```

### `python -m evaluation.assistant_season`

Asks seven season questions (a projected table after Boxing Day, a past champion, the next Manchester derby, most clean sheets and most goals this season, next season, a top scorer). For each it runs the season tool the answer should come from and checks the answer names the expected team and contains no number the tool, the question or today's date don't account for; the last two must be refused (ADR 021).

```sh
LIVE_REFRESH_HOUR=off uv run python -m evaluation.assistant_season
```

All three need the trained model, match history, fixtures, the index and a running Ollama, so they run locally rather than in CI. `LIVE_REFRESH_HOUR=off` stops the app from downloading new data during the run.

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

# All checks, as CI runs them
./gradlew detekt testDebugUnitTest assembleDebug spotlessCheck
```

The app calls the backend at `http://10.0.2.2:8000/v2` (the Android emulator's address for your computer).

---

## Full Pipeline (End-to-End)

Build the served five-league model in sequence from `ai/`:

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

The first backfill downloads every season file, so it takes longer than later runs, which reuse the files already downloaded. Once running, the backend keeps results and fixtures current with its daily refresh.

To add the AI assistant, build its index with `uv run python -m assistant.pipeline --rebuild` (see [AI Assistant Index](#ai-assistant-index)) and restart the backend.
