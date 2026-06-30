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
python -m scripts.ingest_football_data

# Correct
uv run python -m scripts.ingest_football_data
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

### `ERROR: Failed to download dataset` / `httpx.ConnectError`

**Cause:** No internet connection, or `football-data.co.uk` is temporarily unavailable.

**Fix:**
1. Confirm you have internet access.
2. Try opening `https://www.football-data.co.uk/mmz4281/2324/E0.csv` in a browser.
3. If the site is down, wait and retry. The dataset source is external and not under project control.

---

### `ERROR: Validation failed — N rows failed canonical normalisation`

**Cause:** The downloaded CSV contains rows that cannot be normalised to the `ProcessedMatch` schema (bad dates, unrecognised result codes).

**Fix:** This is expected for a small number of rows (preseason or abandoned fixtures). The pipeline logs `Rows skipped: N`. If all 380 rows fail, the source file format has changed — open an issue.

---

### `FileNotFoundError: No processed CSV found in datasets/processed/`

**Cause:** The feature engineering pipeline auto-detects the latest processed CSV. If ingestion has not been run, there is no file to find.

**Fix:** Run ingestion first:
```sh
uv run python -m scripts.ingest_football_data
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

All 142 tests must pass. A failing test will indicate which feature generator has a problem.

---

## Training Issues

### `FileNotFoundError: feature_matrix.parquet not found`

**Cause:** The training pipeline cannot find the feature matrix. Ingestion and feature engineering must be run first.

**Fix:**
```sh
uv run python -m scripts.ingest_football_data
uv run python -m feature_engineering.pipeline
uv run python -m training.pipeline
```

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

### Fewer than 266 tests pass

**Cause:** `uv sync --extra dev` was not run, or a test file has a syntax error.

**Fix:**
```sh
uv sync --extra dev
uv run pytest --tb=long
```

Review any `ERROR` or `FAILED` lines in the output.

---

### Integration test is selected and fails with a network error

**Cause:** The integration test marked `@pytest.mark.integration` requires network access to download live data.

**Fix:** Deselect integration tests for offline runs:
```sh
uv run pytest -m "not integration"
```

This is the default behaviour when running `uv run pytest` without additional flags.

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
