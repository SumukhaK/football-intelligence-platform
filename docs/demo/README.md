# Demo Scripts

Step-by-step walkthroughs of the Football Intelligence Platform for technical interviews and code reviews.

---

## Purpose

These demos are designed for reviewers, recruiters, and interviewers who want to see the platform running end-to-end. Each demo covers one completed stage and can be run independently (given its prerequisites are met).

---

## Available Demos

| Demo | Stage | What you see | Time |
|---|---|---|---|
| [Stage 5 — Data Ingestion](stage-05-demo.md) | 5 | Live download, schema validation, versioned dataset | ~3 min |
| [Stage 6 — Feature Engineering](stage-06-demo.md) | 6 | 9 feature generators, 42-column feature matrix, validation | ~3 min |
| [Stage 7 — Model Training](stage-07-demo.md) | 7 | XGBoost training, evaluation, model card, registry | ~5 min |
| [Stage 8 — SHAP Explainability](stage-08-demo.md) | 8 | Per-prediction SHAP contributions, plots, global summary | ~4 min |
| [Stage 9 — Backend API](stage-09-demo.md) | 9 | FastAPI server, /predict, /explain, OpenAPI docs | ~5 min |
| [Stage 10 — AI Assistant](stage-10-demo.md) | 10 | Build RAG index, chat with assistant, citations | ~8 min |
| [Stage 11 — Android Application](stage-11-demo.md) | 11 | 8-screen Compose Multiplatform app connecting to the backend | ~6 min |
| [Stage 12 — End-to-End Integration](stage-12-demo.md) | 12 | Integration test suite, performance benchmarks, full validation | ~5 min |

---

## Prerequisites

All demos require:

1. A working AI workspace: `cd ai && uv sync --extra dev`
2. An internet connection (Stage 5 only — data download)
3. Ollama installed and running (Stage 10 only)
4. The prior stage's outputs (see each demo for specifics)

---

## Recommended Order

For a full end-to-end demonstration, run the stages in order:

1. Stage 5 — produces the canonical dataset
2. Stage 6 — produces the feature matrix
3. Stage 7 — produces the trained model
4. Stage 8 — produces SHAP explanations
5. Stage 9 — exposes predictions and explanations via REST API
6. Stage 10 — builds and queries the RAG assistant
7. Stage 11 — demonstrates the Android application consuming the backend
8. Stage 12 — runs the integration test suite and validates the full stack

Each stage can also be demonstrated individually using the pre-generated artifacts already committed to the repository.

---

## End-to-End Quick Demo (Stages 7–10)

If the feature matrix and model already exist (pre-generated artifacts are in the repository), run this sequence from `ai/`:

```sh
# Start the backend
uv run uvicorn backend.app.main:app

# In a second terminal — predict a match
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Arsenal", "away_team": "Chelsea", "features": {}}' \
  | python -m json.tool

# Explain the prediction
curl -s -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Arsenal", "away_team": "Chelsea", "features": {}}' \
  | python -m json.tool
```
