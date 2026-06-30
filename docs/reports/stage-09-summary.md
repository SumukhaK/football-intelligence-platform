# Stage 9 Summary — Prediction and Explainability API

**Status:** Complete  
**Date:** 2026-06-30

---

## Objective

Build a production-quality FastAPI backend exposing the Stage 7 (XGBoost) and Stage 8 (SHAP) AI capabilities via a documented REST API. No duplicate AI logic — the backend is a thin adapter layer over the existing AI modules.

---

## What Was Built

### Endpoints

| Method | Path      | Description                                        |
|--------|-----------|----------------------------------------------------|
| GET    | /health   | Reports service health and model availability      |
| GET    | /model    | Returns latest model version and training metrics  |
| POST   | /predict  | Match outcome prediction with class probabilities  |
| POST   | /explain  | Prediction + full SHAP feature contributions       |

### Architecture

- **`backend/app/config.py`** — `pydantic-settings` config; `model_path` and `registry_path` are the only required env vars.
- **`backend/app/main.py`** — FastAPI lifespan loads model and explainer once at startup into `app.state`.
- **`backend/app/dependencies.py`** — `Depends` functions read from `app.state`; raise `ModelNotAvailableError` (503) if not loaded.
- **`backend/app/services/`** — `PredictionService` and `ExplanationService` convert dict→DataFrame, call AI layers, map results to API schemas.
- **`backend/app/exceptions/`** — `ModelNotAvailableError` → 503, `FeatureMissingError` → 422 with `{"missing": [...]}`, `Exception` → 500.
- **`backend/app/middleware/`** — Request logging middleware records method, path, status, and duration.
- **`backend/app/schemas/`** — Pydantic models for all request/response shapes with field-level validation.
- **`backend/app/routers/`** — One router per endpoint; routes are thin — no logic beyond calling the service.

### Integration

The backend lives inside the `ai/` uv workspace at `ai/backend/`, sharing the same venv. FastAPI and uvicorn are dependencies in `ai/pyproject.toml`.

---

## Test Coverage

43 backend tests across 5 files:

| File                     | Tests | What It Covers                                   |
|--------------------------|-------|--------------------------------------------------|
| `test_startup.py`        | 5     | App factory, route registration, OpenAPI schema  |
| `test_health.py`         | 5     | /health responses, model-not-loaded state        |
| `test_model.py`          | 6     | /model responses, missing registry 503           |
| `test_predict.py`        | 9     | Valid predict, field validation, 422, 503        |
| `test_explain.py`        | 8     | Valid explain, field keys, 422, 503              |
| `test_prediction_service.py` | 7 | Service unit tests: mapping, FeatureMissingError |
| `test_explanation_service.py` | 3 | Service unit tests: mapping, FeatureMissingError|

Total project tests: **363 passed**.

---

## Code Quality

- `ruff check .` — 0 errors
- `black --check .` — 0 changes needed
- `mypy .` — 0 errors (154 source files)
- All tests pass in ~73s

---

## Manual Verification

Server started with `uv run uvicorn backend.app.main:app --reload`:

```
INFO: Prediction model loaded: version=20260630_132617
INFO: Explanation service loaded.
INFO: Application startup complete.
```

- `GET /health` → `{"status": "ok", "model_loaded": true, "explainability_available": true}`
- `GET /model` → returns model version, dataset version, git commit, and 6 training metrics
- `POST /predict` → `{"predicted_result": "H", "probability_home": 0.427, "confidence": 0.427, ...}`
- `POST /explain` → prediction + 42 SHAP contributions, 10 top positive, 10 top negative features
- `GET /docs` → Swagger UI with all endpoints and schemas

---

## Decisions

- Backend code lives in `ai/backend/` (same uv workspace) to avoid a separate venv and numpy/meson build failures with standalone `backend/pyproject.toml`.
- `app.state` is the dependency container — no global variables, no singletons.
- Services receive `object` typed AI adapters to avoid importing AI classes at module load time; `# type: ignore[attr-defined]` suppresses mypy's attr check.
- 503 tests use `patch` on `_settings` and `get_settings` so the lifespan skips loading the real model and `app.state` stays `None`.
