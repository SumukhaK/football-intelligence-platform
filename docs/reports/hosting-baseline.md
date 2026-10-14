# Hosting baseline

Measured 14 October 2026 on the developer PC (Windows, Docker Desktop 29.8.2, 16 CPUs, 7.5 GiB given to Docker), from `develop` at the commit that added this report. Hosting tracker step 0. Cloud numbers come later, from staging (step 6).

## Code checks

From `ai/`: `ruff check`, `black --check` and `mypy` (strict) are clean. `pytest -m "not integration"` passes with 84% coverage (the gate is 70%). One test, `test_health_no_model_loaded`, fails only on machines that have a real assistant index, because it expects the assistant to be unavailable; CI has no index and passes it.

The frontend's `assembleDebug`, `testDebugUnitTest`, `detekt` and `spotlessCheck` pass, and a shrunk release build works end to end on an emulator (tracker step 5a).

## Image

| | |
|---|---|
| Image | `football-api`, built by the root `Dockerfile` (ADR 025) |
| Size | 2.44 GB uncompressed |
| Snapshot | 8 files (models, registry, newest results and fixtures, Workers AI index), verified at build time |
| User | UID 10001, files read-only |

Most of the size is the scientific stack (SHAP, numba, scikit-learn, XGBoost, pandas, pyarrow).

## Startup with `LIVE_REFRESH_HOUR=off` and the assistant off

Time from container start to "Application startup complete", read from the JSON logs' timestamps, and the `duration_ms` of each `component.load` event.

| Run | Imports (start to first log line) | Loading (first log line to ready) | Total |
|---|---|---|---|
| First run of a freshly built image | about 3 min | 43 s | about 3 min 45 s |
| Same image, files already cached | 3 s | 2.3 s | 5.5 s |

Component load times (ms):

| Component | First run | Cached |
|---|---|---|
| `match_history` | 15,248 | 140 |
| `goals_model` (Dixon-Coles fits, 5 leagues) | 5,253 | 369 |
| `season_outlook` | 5,616 | 151 |
| `prediction_model` | 5,746 | 272 |
| `explanation` (SHAP) | 10,438 | 1,167 |
| `season_history` | 261 | 154 |
| `fixtures` | 9 | 14 |

The first run is dominated by reading a cold 2.4 GB image from disk under Docker Desktop; with the files cached the whole boot takes 5.5 s. Fitting the goals models is not the bottleneck (0.4 s cached), so precomputing them (plan phase 2, point 6) isn't needed on this evidence.

**What this means for Cloud Run.** A new Cloud Run instance pulls the image fresh, so its first boot may look more like the first run than the cached one, and Cloud Run requires the server to listen within 4 minutes. That makes the cold boot the first number to measure on staging (step 6). If it is too slow, the cheapest fix is a smaller image, before tuning anything else.

## Memory

| State | Container memory |
|---|---|
| Ready, idle | 257 to 312 MiB |
| After a prediction | 269 MiB |

The trial setting of 1 vCPU and 1 GiB leaves plenty of headroom. With the assistant on, the hosted index adds about 2 MB.

## Served correctly

From the running container: `/v2/ready` answered `{"status":"ready"}`, `/v2/fixtures` returned the next Premier League round, and `POST /v2/predict` returned Everton v Chelsea from model `20261007_154105`. Writing to `/app/ai` failed with "Permission denied", as intended.
