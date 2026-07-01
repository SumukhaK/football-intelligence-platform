# Demo Script — Football Intelligence Platform

Three ready-to-run demo scripts, scaled to the time available. All assume the prerequisites below are already satisfied — see [docs/demo/stage-12-demo.md](../demo/stage-12-demo.md) for full environment setup if starting from scratch.

---

## Prerequisites (all scripts)

```sh
# Backend dependencies + model artifacts
cd ai && uv sync --extra dev
ls models/latest/model.joblib   # must exist — if not, run the training pipeline first

# Start the backend
uv run uvicorn backend.app.main:app --reload
```

Optional (for the assistant demo): Ollama running with `nomic-embed-text` and `llama3.2` pulled, and the assistant index built (`uv run python -m assistant.pipeline --rebuild`).

For the Android segments: an emulator running, app installed (`cd frontend && ./gradlew assembleDebug && adb install app/build/outputs/apk/debug/app-debug.apk`).

---

## 5-Minute Demo

**Audience:** Recruiters, non-technical stakeholders, quick screen-share.
**Goal:** Show that this is a real, working, end-to-end product — not a notebook.

| Time | Talking Point | Action |
|---|---|---|
| 0:00–0:30 | "This is an AI football analytics platform — predicts match outcomes, explains every prediction, and answers questions about its own data, all running locally." | Show the running backend terminal (`Uvicorn running on...`) |
| 0:30–1:30 | "Here's the API documentation, auto-generated — five endpoints." | Open `http://127.0.0.1:8000/docs`, briefly expand `/predict` and `/explain` |
| 1:30–3:00 | "Here's the mobile app, talking to that exact backend." | Open the Android app Home screen → show green status chips → tap Predict Match → select two teams → tap Predict |
| 3:00–4:00 | "Every prediction comes with an explanation — not a black box." | Tap Explain This Prediction → show positive/negative SHAP features |
| 4:00–5:00 | "462 tests pass, including 36 that run against the actual trained model, not mocks." | Show `docs/reports/stage-12-summary.md` Testing Summary table, or run `uv run pytest tests/integration/ -v` live if time allows |

**Expected outputs:** A prediction (H/D/A) with three probabilities; a SHAP explanation with positive and negative feature lists; `/docs` showing 5 endpoints.

---

## 10-Minute Demo

**Audience:** Hiring managers, technical recruiters with some ML/backend familiarity.
**Goal:** Show the system end-to-end and touch each major component's reasoning.

| Time | Talking Point | Action / Command |
|---|---|---|
| 0:00–1:00 | Project framing: "Most ML demos stop at a notebook accuracy number. This one asks what it takes to ship a model as an explainable, grounded, mobile-usable product." | — |
| 1:00–2:30 | Data pipeline: leakage-safe features, chronological split. | `cat ai/datasets/features/feature_matrix.parquet` schema, or open `docs/adr/003-chronological-train-val-test-split.md` |
| 2:30–4:00 | Model + explainability: "56% accuracy, 33% random baseline, every prediction explained via SHAP." | `POST /predict` then `POST /explain` via `/docs` "Try it out", or via curl: `curl -X POST localhost:8000/predict -d '{...}'` |
| 4:00–6:00 | Android app: full prediction → result → explain flow. | Live on emulator |
| 6:00–7:30 | AI assistant: grounded RAG, not a raw LLM call. | Ask the assistant "What is the model's test accuracy?" → show the cited source in the answer |
| 7:30–9:00 | Testing philosophy: mocked contract tests vs. real-model integration tests. | `uv run pytest tests/integration/ -v` — show 36 tests passing against the real model |
| 9:00–10:00 | Wrap-up: architecture diagram, ADRs, 12-stage build process. | Show root README architecture diagram |

**Expected outputs:** Same as the 5-minute demo, plus a grounded assistant answer with a citation, plus a visible integration test run.

---

## 20-Minute Technical Walkthrough

**Audience:** Engineering interviewers, technical deep-dive.
**Goal:** Demonstrate engineering judgment and trade-off reasoning, not just feature completeness.

| Time | Talking Point | Action / Command |
|---|---|---|
| 0:00–1:30 | Project framing and the 12-stage build process. | Show `docs/showcase/project-timeline.md` |
| 1:30–4:00 | Data pipeline deep dive: provider abstraction, schema validation, leakage prevention via `.shift(1)`, Kahn's topological sort for feature dependencies. | Walk through `ai/feature_engineering/` source briefly; reference [ADR 003](../adr/003-chronological-train-val-test-split.md) |
| 4:00–7:00 | Model training: chronological split, `TimeSeriesSplit` CV, model registry with git-commit traceability. | `cat ai/models/registry.json`; open `ai/models/latest/model_card.md` |
| 7:00–10:00 | Explainability deep dive: why `TreeExplainer` over LIME, the `ExplainerCache`, multi-class SHAP normalisation, measured ~7ms latency. | Reference [ADR 004](../adr/004-shap-for-explainability.md); show `POST /explain` response shape |
| 10:00–13:00 | RAG pipeline: chunking, embedding, retrieval, relevance filtering, source-constrained prompting, graceful 503 degradation. | Ask the assistant a question; then stop Ollama and show the same request returning a clean 503, not a crash |
| 13:00–16:00 | Backend architecture: lifespan DI, structured exception handling, the 422 vs 503 distinction, OpenAPI accuracy. | Walk through `ai/backend/app/main.py` lifespan function |
| 16:00–18:00 | Android architecture: MVVM with StateFlow, Koin DI, ViewModel sharing across the Prediction → Result → Explain flow via back-stack scoping. | Walk through `frontend/feature-prediction/src/androidMain/.../PredictionViewModel.kt` |
| 18:00–19:30 | Testing strategy: 426 mocked contract tests vs. 36 real-model integration tests — what each catches that the other can't. | `uv run pytest -m "not integration"` then `uv run pytest tests/integration/ -v` — show both passing separately |
| 19:30–20:00 | Known limitations and what's next: neutral Android features, single-season data, no auth. | Reference root README "Future Improvements (Out of Scope)" |

**Expected outputs:** All of the above, plus visible proof of graceful degradation (503 without crashing) and a clear two-tier test run demonstrating the testing philosophy.

---

## Troubleshooting During a Live Demo

| Symptom | Fix |
|---|---|
| Backend won't start — model not found | Run `uv run python -m training.pipeline` first, or use a pre-trained `models/latest/` if available |
| Android app can't reach backend | Emulator must use `10.0.2.2`, not `localhost`; confirm backend is bound to `0.0.0.0` or `127.0.0.1:8000` |
| Assistant always returns 503 | Expected if Ollama isn't running — frame this as a feature ("watch it degrade gracefully") rather than a failure |
| Integration tests fail | Almost always means `models/latest/model.joblib` is missing — they auto-skip if so; re-run the training pipeline |
