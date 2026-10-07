# Troubleshooting Guide

Common issues and their solutions for the Football Intelligence Platform.

---

## Python / uv Issues

### `uv: command not found`

**Cause:** uv is not installed or not on your `PATH`.

**Fix:**
```sh
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal after installation.

---

### `Python 3.12 not found` or `Requires Python >=3.12`

**Cause:** uv cannot find a Python 3.12 interpreter.

**Fix:**
```sh
uv python install 3.12
```

uv will download and manage the Python version automatically. You do not need to install Python separately.

---

### `uv sync` fails with dependency resolution errors

**Cause:** Network issue or a transient upstream package registry problem.

**Fix:**
```sh
# Clear uv cache and retry
uv cache clean
uv sync --extra dev
```

---

### `ModuleNotFoundError` when running pipeline commands

**Cause:** You ran the command without `uv run`, so the project's virtual environment was not activated.

**Fix:** Always prefix pipeline commands with `uv run`:
```sh
# Wrong
python -m scripts.backfill_football_data --base-dir ../datasets --confirm

# Correct
uv run python -m scripts.backfill_football_data --base-dir ../datasets --confirm
```

---

### `mypy` reports `Cannot find implementation or library stub`

**Cause:** A third-party library was installed but its stubs package was not.

**Fix:** Run from the `ai/` directory:
```sh
uv sync --extra dev
```

The `dev` extras include `pandas-stubs`. All other overrides are in `pyproject.toml` under `[[tool.mypy.overrides]]`.

---

## Data Ingestion Issues

### `FAILED: ...` when downloading data

**Cause:** No internet connection, or `football-data.co.uk` is temporarily unavailable.

The download scripts report it like this:
- `scripts.backfill_football_data`, `scripts.refresh_live_dataset` and `scripts.refresh_fixtures` print `FAILED: <reason>` and exit with code 1.
- The legacy `scripts.ingest_football_data` prints `Downloading... FAILED` followed by `Error: <reason>`.

**Fix:**
1. Confirm you have internet access.
2. Try opening `https://www.football-data.co.uk/mmz4281/2324/E0.csv` in a browser.
3. If the site is down, wait and retry. The dataset source is external and not under project control. The backfill reuses files it already downloaded, so a retry only fetches what is missing.

---

### Rows skipped, or `All N rows failed canonical normalisation`

**Cause:** The downloaded CSV contains rows that cannot be normalised to the `ProcessedMatch` schema (bad dates, unrecognised result codes).

**Fix:** A few skipped rows are expected (the legacy ingestion prints `Rows skipped: N`; the backfill fails the run if more than 0.5% of any season's rows cannot be parsed). If every row of a file fails, the source file format has changed — open an issue.

---

### `ERROR: No canonical CSV found matching '...' relative to '...'.`

**Cause:** `feature_engineering.pipeline` was run without `--input`. Its default only looks for legacy single-season files (`datasets/processed/football_data/match_results_v*.csv`, relative to `ai/`), not the five-league dataset.

**Fix:** Build the five-league dataset if you have not, then pass it explicitly:
```sh
uv run python -m scripts.backfill_football_data --base-dir ../datasets --confirm
uv run python -m feature_engineering.pipeline --input ../datasets/processed/football_data/match_results_top5_v<ts>.csv --output-dir ../datasets/features/top5
```

---

## Feature Engineering Issues

### `RegistryError: Cycle detected in feature dependency graph`

**Cause:** A feature generator declares a dependency that creates a circular dependency chain in the `FeatureRegistry`.

**Fix:** This should not happen with the default feature set. If you have added a custom feature generator, review its `dependencies` attribute to ensure it does not reference a feature that (directly or indirectly) depends on it.

---

### `Validation: FAILED` with warnings about NaN values

**Cause:** One or more feature generators produced unexpected NaN values outside the expected first-match rows.

**Fix:** Review the warning messages printed by the pipeline. NaN values in the first row per team for rolling features are expected and acceptable. Unexpected NaN values in later rows indicate a bug in the feature generator.

---

### Feature matrix has fewer than 42 columns

**Cause:** A feature generator was not registered, or registration failed silently.

**Fix:**
```sh
uv run pytest tests/feature_engineering/
```

All 91 tests must pass. A failing test will indicate which feature generator has a problem.

---

## Training Issues

### `ERROR: [Errno 2] No such file or directory: ...feature_matrix.parquet`

**Cause:** The training pipeline cannot find the feature matrix. Its default path (`datasets/features/feature_matrix.parquet`, relative to `ai/`) is not where the five-league matrix is written.

**Fix:** Build the matrix and pass its path:
```sh
uv run python -m scripts.backfill_football_data --base-dir ../datasets --confirm
uv run python -m feature_engineering.pipeline --input ../datasets/processed/football_data/match_results_top5_v<ts>.csv --output-dir ../datasets/features/top5
uv run python -m training.pipeline --feature-matrix ../datasets/features/top5/feature_matrix.parquet --split-strategy season --val-seasons 2022/23 --test-seasons 2023/24 --holdout-seasons 2024/25 2025/26 --max-depth 3 --learning-rate 0.03 --n-estimators 400
```

The same applies to `explainability.pipeline`: pass `--feature-matrix ../datasets/features/top5/feature_matrix.parquet`.

---

### Training completes with very low accuracy (below 0.40)

**Cause:** Early stopping triggered too early, or the feature matrix contains data leakage from post-match statistics.

**Fix:** Verify that `feature_matrix.parquet` contains only pre-match features. The 42-column matrix produced by the default pipeline excludes all post-match statistics. If you have added custom features, ensure they do not use `full_time_home_goals`, `full_time_away_goals`, `result`, or any other column that is only known after the match is played.

---

### `DeprecationWarning: Setting the shape on a NumPy array has been deprecated`

**Cause:** joblib 1.5.x + NumPy 2.5.x version interaction. This is a known upstream issue.

**Impact:** Tests pass. The warning is cosmetic and does not affect correctness.

**Fix:** No action needed. Will be resolved by a future joblib release.

---

### `models/registry.json` contains Windows absolute paths

**Cause:** The registry stores the `run_dir` as an absolute path on the machine that ran training.

**Impact:** The `run_dir` field in `registry.json` is informational. The `models/latest/` directory always contains the correct relative artifacts.

**Fix:** When running on a different machine, re-run `uv run python -m training.pipeline` to generate a new registry entry with the correct local path.

---

## Pytest Issues

### Fewer than 872 tests pass

**Cause:** `uv sync --extra dev` was not run, or a test file has a syntax error.

**Fix:**
```sh
uv sync --extra dev
uv run pytest --tb=long
```

Review any `ERROR` or `FAILED` lines in the output.

---

### Integration tests fail on a clean checkout or offline

**Cause:** 37 tests are marked `@pytest.mark.integration`. They need the trained model in `ai/models/latest/`, and one of them downloads live data.

**Fix:** Train the model (see the [quick start](setup/quick-start.md)), or skip them:
```sh
uv run pytest -m "not integration"
```

This is not the default: `uv run pytest` runs every test, including integration tests.

---

## Backend Issues

### `429 Too many requests`

**Cause:** A client made more than 120 requests in one minute (`RATE_LIMIT_PER_MINUTE`).

**Fix:** Wait the number of seconds in the `Retry-After` header and retry. For local load testing, raise the limit or set `RATE_LIMIT_PER_MINUTE=off` in `ai/.env`. Health checks and the docs are never limited.

---

### `503 Match features not available`

**Cause:** The server could not load match history, so it cannot compute features for a prediction. The detail reads `Match history is not loaded. Check MATCHES_DIR in configuration.` At startup the log shows `Match history not loaded from ...`, and `/v2/health` shows `"fixture_features_available": false`.

**Fix:**
1. Build the match history with `uv run python -m scripts.backfill_football_data --base-dir ../datasets --confirm`, or bring it up to date with `uv run python -m scripts.refresh_live_dataset --confirm`.
2. Check that `MATCHES_DIR` (default `../datasets/processed/football_data`) points at the folder with the `match_results_top5_v*.csv` or `match_results_live_v*.csv` files.
3. Restart the backend.

---

### Daily refresh fails

**Cause:** The server downloads the latest results and fixtures every day at `LIVE_REFRESH_HOUR` (default 6). Without network access, or when a source is down, the download fails. The server keeps serving the data it already has.

**Fix:** Check `last_refresh_error` in `curl http://localhost:8000/v2/health`; it says why the last refresh failed and is `null` after a success. To work offline, set `LIVE_REFRESH_HOUR=off` in `ai/.env` and restart. To refresh by hand later, run `uv run python -m scripts.refresh_live_dataset --confirm`.

---

### Fixtures are missing (`503 Fixtures not available`)

**Cause:** No upcoming-fixtures file exists in `FIXTURES_DIR` (default `../datasets/processed/openfootball`). When the daily refresh is on, the server tries to download fixtures at startup if it has none, which needs network access.

**Fix:**
```sh
uv run python -m scripts.refresh_fixtures --confirm
```

Then restart the backend.

---

### `/predict` gives different results from `/v2/predict`

**Cause:** `/predict` (no prefix) and `/v1/predict` are the frozen v1.0.0 contract. They use the original Premier League model (`V1_MODEL_PATH`) and accept only the Premier League; naming another league returns 422 `Unknown competition`.

**Fix:** Call `/v2/predict` for the current five-league model. Send only the team names and, optionally, `competition`. Do not send `"features": {}`: an empty object counts as supplied features and fails with 422. See [`docs/api.md`](api.md).

---

## Android / Gradle Issues

### `SDK location not found`

**Cause:** Gradle cannot find the Android SDK because `local.properties` is missing.

**Fix:** Create `frontend/local.properties` with your SDK path:
```
# macOS
sdk.dir=/Users/<username>/Library/Android/sdk

# Windows
sdk.dir=C\:\\Users\\<username>\\AppData\\Local\\Android\\Sdk

# Linux
sdk.dir=/home/<username>/Android/Sdk
```

---

### `Unsupported class file major version N`

**Cause:** Gradle is running on a JDK that is too old. This project requires JDK 17+.

**Fix:**
1. Install JDK 17 or higher.
2. Set `JAVA_HOME` to point to the new JDK.
3. Verify: `java -version` should show `17.x` or higher.

---

### `Deprecated Gradle features were used in this build`

**Cause:** Some Gradle plugins use deprecated APIs. This is a known issue with the current Gradle 8.8 + Kotlin plugin combination.

**Impact:** Build succeeds. The warning is informational.

**Fix:** No action needed. The deprecations will be resolved in a future plugin update.

---

### Build fails with `Could not resolve` dependency errors

**Cause:** Gradle cannot reach Maven Central or Google's Maven repository.

**Fix:** Check your internet connection. On corporate networks, you may need to configure a proxy in `gradle.properties`:
```properties
systemProp.http.proxyHost=proxy.example.com
systemProp.http.proxyPort=8080
```

---

### `./gradlew: Permission denied` (macOS/Linux)

**Cause:** The Gradle wrapper script is not executable.

**Fix:**
```sh
chmod +x frontend/gradlew
```

---

### Android app shows the offline banner

**Cause:** The app cannot reach the backend at `http://10.0.2.2:8000/v2` (the emulator's address for your computer), so it shows the data it saved last time.

**Fix:** Start the backend from `ai/` with `uv run uvicorn backend.app.main:app --reload`, then pull down to refresh.

---

## CI Issues

### Frontend checks did not run on a pull request

**Cause:** The frontend workflows run only on pull requests into `main` (and pushes to `main`) that change `frontend/`. Pull requests into other branches skip them.

**Fix:** Run the same checks locally from `frontend/`:
```sh
./gradlew detekt testDebugUnitTest assembleDebug spotlessCheck
```

---

### CI fails with `./gradlew: Permission denied`

**Cause:** `frontend/gradlew` lost its executable bit in git, often after a commit from Windows.

**Fix:**
```sh
git update-index --chmod=+x frontend/gradlew
```

Commit the change. `git ls-files -s frontend/gradlew` should show mode `100755`.

---

## Platform-Specific Issues

### Windows: `uv run` command hangs in Git Bash

**Cause:** Git Bash has known issues with interactive Python processes.

**Fix:** Use PowerShell instead of Git Bash for all uv commands on Windows.

---

### macOS: `SSL: CERTIFICATE_VERIFY_FAILED`

**Cause:** Python's SSL certificates are not installed.

**Fix:**
```sh
# Run the Install Certificates script included with Python
/Applications/Python\ 3.12/Install\ Certificates.command
```

---

### Linux: `libgomp` not found when loading XGBoost model

**Cause:** OpenMP runtime is missing on some minimal Linux installations.

**Fix:**
```sh
# Ubuntu/Debian
sudo apt-get install libgomp1

# CentOS/RHEL
sudo yum install libgomp
```
