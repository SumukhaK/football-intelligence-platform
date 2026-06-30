# Backend

FastAPI application exposing match outcome predictions, SHAP explanations, and model metadata through a documented REST API.

---

## Ownership

Backend implementation. Follows the standards defined in `.claude/CLAUDE.md` section 8.

---

## Architecture

Clean Architecture with strict layer separation. The application code lives inside the `ai/` Python workspace at `ai/backend/`.

- **Schemas:** Pydantic request/response models with field-level validation.
- **Services:** Thin adapters that convert API types to AI-layer types and back.
- **Routers:** FastAPI route handlers — no business logic, only HTTP concerns.
- **Dependencies:** FastAPI `Depends` functions that read from `app.state`.
- **Lifespan:** Model and explainer loaded once at startup; stored on `app.state`.

---

## Directory Structure

```
ai/backend/
  app/
    config.py           # pydantic-settings configuration (model_path, registry_path)
    dependencies.py     # Depends functions for PredictionService and ExplanationService
    main.py             # FastAPI app factory and lifespan startup
    exceptions/
      __init__.py       # ModelNotAvailableError, FeatureMissingError, handlers
    middleware/
      __init__.py       # Request logging middleware
    routers/
      health.py         # GET /health
      model.py          # GET /model
      prediction.py     # POST /predict
      explainability.py # POST /explain
    schemas/
      common.py         # HealthResponse, ModelInfoResponse, ErrorResponse
      prediction.py     # PredictionRequest, PredictionResponse
      explainability.py # ExplanationResponse, FeatureContributionSchema
    services/
      prediction_service.py   # Wraps MatchPredictor for route handlers
      explanation_service.py  # Wraps AI ExplanationService for route handlers
```

---

## Running Locally

```bash
cd ai
uv run uvicorn backend.app.main:app --reload
```

The server starts on `http://127.0.0.1:8000`. Interactive docs at `/docs`.

---

## API Endpoints

| Method | Path      | Description                                  |
|--------|-----------|----------------------------------------------|
| GET    | /health   | Service health and model availability        |
| GET    | /model    | Latest model version and training metrics    |
| POST   | /predict  | Match outcome prediction with probabilities  |
| POST   | /explain  | Prediction + SHAP feature contributions      |

### Error Responses

All errors return structured JSON:
```json
{ "error": "...", "detail": "..." }
```

| HTTP | Condition                        |
|------|----------------------------------|
| 422  | Validation failure or missing features |
| 503  | Model not loaded                 |
| 500  | Unexpected server error          |

---

## Configuration

Set via environment variables or `.env` file:

| Variable        | Default                              | Description              |
|-----------------|--------------------------------------|--------------------------|
| `MODEL_PATH`    | `../ai/models/latest/model.joblib`   | Path to trained model    |
| `REGISTRY_PATH` | `../ai/models/registry.json`         | Path to model registry   |
| `API_VERSION`   | `0.1.0`                              | Version string in /health|
| `LOG_LEVEL`     | `INFO`                               | Logging level            |

---

## Testing

Tests live at `ai/tests/backend/`. Run from the `ai/` directory:

```bash
cd ai
uv run pytest tests/backend/ -v
```

43 tests cover: health, model, predict, explain, startup, error paths, and service units.

---

## Development Standards

- One router per domain area. Routers contain no business logic.
- Service classes adapt AI types to API types. No ML logic in services.
- All request and response bodies are Pydantic models with field-level validation.
- Errors return structured JSON: `{ "error": "...", "detail": "..." }`.
- All endpoints have OpenAPI docstrings.
- Environment config via `pydantic-settings`. No `os.environ` in code.
