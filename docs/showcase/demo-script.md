# Demo Script — Football Intelligence Platform

Three ready-to-run demo scripts, scaled to the time available. If you only need to show it, the [3-minute narrated demo video](demo-video/README.md) covers the whole system. For setup from scratch, follow the Quick Start in the [root README](../../README.md#quick-start).

---

## Prerequisites (all scripts)

```sh
# Backend dependencies + model artifacts (built by the README Quick Start)
cd ai && uv sync --extra dev
ls models/latest/model.joblib                       # the current five-league model
ls models/runs/20260630_132617/model.joblib         # the original model, served by /v1
ls ../datasets/processed/football_data/             # match history for server-side features
uv run python -m scripts.refresh_fixtures --confirm # upcoming fixtures, if you have none yet

# Start the backend (LIVE_REFRESH_HOUR=off keeps it from downloading during the demo)
LIVE_REFRESH_HOUR=off uv run uvicorn backend.app.main:app --host 0.0.0.0 --reload
```

Optional (for the assistant demo): Ollama running with `nomic-embed-text` and `llama3.2` pulled, and the assistant index built (`uv run python -m assistant.pipeline --rebuild`).

For the Android segments: an emulator running, app installed (`cd frontend && ./gradlew assembleDebug && adb install app/build/outputs/apk/debug/app-debug.apk`).

---

## 5-Minute Demo

**Audience:** Recruiters, non-technical stakeholders, quick screen-share.
**Goal:** Show that this is a real, working, end-to-end product — not a notebook.

| Time | Talking Point | Action |
|---|---|---|
| 0:00–0:30 | "This is an AI football analytics platform for Europe's top five leagues — it predicts matches, explains every prediction, and answers questions about its own data, all running locally." | Show the running backend terminal |
| 0:30–1:30 | "The app opens on upcoming fixtures, one tab per league, in my time zone." | Android app: Fixtures tab, switch from Premier League to Bundesliga |
| 1:30–3:00 | "Pick a league and two teams, and the real model answers." | Predict tab → league → teams → **Predict Match Outcome** → show probabilities, the draw tag if shown, and the likely scores |
| 3:00–4:00 | "Every prediction comes with an explanation — not a black box." | Tap **Explain** → show "Why the model leans this way" and "What counts against it" |
| 4:00–5:00 | "It's close to the bookmakers using only public results, and 871 tests keep it honest." | Mention 52.5% vs 55.0% for bookmakers; open `docs/releases/v2.0.0.md` if asked |

**Expected outputs:** A fixtures list by date; a prediction with three probabilities and likely scores; a plain-language explanation.

---

## 10-Minute Demo

**Audience:** Hiring managers, technical recruiters with some ML/backend familiarity.
**Goal:** Show the system end-to-end and touch each major component's reasoning.

| Time | Talking Point | Action / Command |
|---|---|---|
| 0:00–1:00 | Project framing: "Most ML demos stop at a notebook accuracy number. This one asks what it takes to ship a model as an explainable, grounded, mobile-usable product." | — |
| 1:00–2:30 | Data: 46,709 matches, five leagues, leakage-safe features, season-based split. | Open [ADR 007](../adr/007-season-based-split-and-evaluation.md) |
| 2:30–4:00 | Model + explainability: "52.5% on a test season, 33% random, 55% bookmakers; every prediction explained via SHAP." | `/docs` → `POST /v2/predict` then `POST /v2/explain`, or curl (below) |
| 4:00–6:00 | Android app: fixtures, prediction → result → explain, then offline mode. | Live on emulator; stop the backend and pull to refresh to show the offline banner |
| 6:00–7:30 | AI assistant: grounded RAG, not a raw LLM call. | Ask "What is the model's test accuracy?" → show the cited source |
| 7:30–9:00 | Testing philosophy: mocked contract tests vs. real-model integration tests. | `uv run pytest tests/integration/ -v` — 36 tests against the real model |
| 9:00–10:00 | Wrap-up: architecture diagram, ADRs, versioned API. | Show the root README architecture diagram |

```sh
curl -s -X POST localhost:8000/v2/predict -H "Content-Type: application/json" \
  -d '{"home_team": "Arsenal", "away_team": "Chelsea", "competition": "Premier League"}' | python -m json.tool
```

**Expected outputs:** Same as the 5-minute demo, plus a grounded assistant answer with a citation, plus a visible integration test run.

---

## 20-Minute Technical Walkthrough

**Audience:** Engineering interviewers, technical deep-dive.
**Goal:** Demonstrate engineering judgment and trade-off reasoning, not just feature completeness.

| Time | Talking Point | Action / Command |
|---|---|---|
| 0:00–1:30 | Project framing: 12 build stages to v1.0.0, then the v2 releases. | Show `docs/showcase/project-timeline.md` |
| 1:30–4:00 | Data pipeline: provider abstraction, immutable raw files, season-integrity validation, leakage prevention via `.shift(1)`, Kahn's topological sort for feature dependencies. | Walk through `ai/feature_engineering/`; reference [ADR 006](../adr/006-team-canonicalisation-and-match-dedup.md) |
| 4:00–7:00 | Model training and evaluation: season split, walk-forward tuning, bookmaker benchmark, bootstrap promotion rule, the draw analysis. | Open `docs/reports/multi-league-retraining-comparison.md` and `docs/reports/draw-handling.md` |
| 7:00–10:00 | Explainability and scores: why `TreeExplainer` over LIME, the `ExplainerCache`, fan-friendly labels; the Dixon-Coles goals model. | Show `POST /v2/explain` and `POST /v2/insights` responses |
| 10:00–13:00 | RAG pipeline: chunking, embedding, retrieval, source-constrained prompting, graceful 503 degradation. | Ask the assistant a question; then stop Ollama and show the same request returning a clean 503 |
| 13:00–16:00 | Backend architecture: lifespan DI, server-side features, daily refresh without restart, `/v1` vs `/v2`, rate limiting, 422 vs 503 vs 429. | Walk through `ai/backend/app/main.py`; call `/predict` (v1 model) and `/v2/predict` (current model) side by side |
| 16:00–18:00 | Android architecture: MVVM with StateFlow, Koin DI, the caching decorator for offline mode, ViewModel sharing across Prediction → Result → Explain. | Walk through `frontend/core-network/.../CachingFootballApiService.kt` and `PredictionViewModel.kt` |
| 18:00–19:30 | Testing strategy: 762 unit and contract tests vs. 36 real-model integration tests, plus 73 Android tests. | `uv run pytest -m "not integration"` then `uv run pytest tests/integration/ -v` |
| 19:30–20:00 | Known limitations and what's next: no authentication, no automated assistant evaluation, results-only data. | Reference the "Future Scope" section of [project-showcase.md](project-showcase.md) |

**Expected outputs:** All of the above, plus visible proof of graceful degradation (503 without crashing) and a clear two-tier test run.

---

## Troubleshooting During a Live Demo

| Symptom | Fix |
|---|---|
| Backend starts but `/v2/predict` returns 503 "Model not available" | Build the model with the README Quick Start commands (the no-argument `training.pipeline` builds the old single-season model) |
| `/v2/predict` returns 503 "Match features not available" | No match history: run the backfill, or `uv run python -m scripts.refresh_live_dataset --confirm` |
| Fixtures tab shows an error | Run `uv run python -m scripts.refresh_fixtures --confirm`, then restart the backend |
| Android app can't reach backend | Emulator must use `10.0.2.2`; start uvicorn with `--host 0.0.0.0` |
| Assistant always returns 503 | Expected if Ollama isn't running — frame it as graceful degradation |
| Integration tests skip or fail | `models/latest/model.joblib` is missing; re-run the training pipeline |
