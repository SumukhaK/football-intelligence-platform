# Portfolio Summary — Football Intelligence Platform

*A two-page summary for recruiters and hiring managers.*

---

## Project Overview

The Football Intelligence Platform is a complete, working AI system for Europe's top five football leagues. It predicts match outcomes, explains every prediction in plain football language, estimates likely scores, lists upcoming fixtures, answers natural-language questions grounded in its own documents, and serves all of this through a native Android app. One engineer built it end to end: 12 stages up to v1.0.0, then the v2 releases.

It is not a notebook or a prototype. It is a tested (945 tests), documented, reproducible system that runs entirely on a laptop with zero cloud dependency: a Python ML pipeline, a versioned FastAPI backend, a local RAG assistant powered by Ollama, and a Compose Multiplatform Android client. A [3-minute demo video](demo-video/README.md) shows it end to end.

**The goal was never "build a model." It was "ship a model as a trustworthy, explainable, usable product."**

---

## Technical Challenges

| Challenge | Solution |
|---|---|
| Time-series leakage in rolling-window features | `.shift(1)` on every rolling feature and a whole-season train/validation/test split with holdout seasons |
| Knowing whether a better score is real | Benchmarked against bookmaker odds, and promoted models only when a paired bootstrap interval excluded zero |
| Training/serving skew | The server builds all 42 features from match history with the training pipeline; clients send only team names |
| Draws the model never picks | Showed the draw probability is calibrated but flat, and added a "draw possible" tag instead of forcing picks |
| Preventing LLM hallucination without fine-tuning | Source-only system prompt, retrieval grounding, citations, and a fixed "not enough information" reply |
| Keeping old clients working after a breaking change | Path-versioned API: `/v1` keeps the v1.0.0 contract and model, `/v2` serves five leagues |
| A mobile app that stays useful offline | A caching decorator replays saved answers with an offline banner; server errors are still shown |

---

## Architecture Decisions

Sixteen ADRs record every structural decision (`docs/adr/`). The most important:

1. **XGBoost** for prediction — strong tabular baseline with exact SHAP `TreeExplainer` support.
2. **Five leagues, 26 seasons** — data mattered far more than tuning.
3. **Season-based split and evaluation** — the realistic way to test a time-ordered sports model.
4. **Server-side features** — one code path for training and serving.
5. **Dixon-Coles goals model** for likely scores, **draw tag** for tight games.
6. **Daily in-process refresh, API versions and a rate limiter** — fresh data, stable contracts, protection from runaway clients.

Beyond the ADRs: Clean Architecture with one-directional dependencies in both the Python backend and the Kotlin frontend; MVVM with `StateFlow` on Android; lifespan-based dependency injection in FastAPI.

---

## AI Components

- **XGBoost classifier** — `multi:softprob`, 42 pre-match features, 46,709 matches, tuned by season walk-forward CV. Test 2023/24: 52.5% accuracy and log loss 0.976 (random 33.3%; bookmakers 55.0% and 0.955). Live 2026/27 check: 52.4% against 51.6% for bookmaker favourites.
- **SHAP explainability** — per-prediction attribution through `POST /v2/explain`, with fan-friendly labels for every feature.
- **Dixon-Coles goals model** — likely scores, expected goals and goal markets through `POST /v2/insights`, refitted daily.
- **Retrieval-Augmented Generation** — Ollama embeddings (`nomic-embed-text`) into a numpy vector store, cosine retrieval, and a source-constrained system prompt feeding `llama3.2`.
- **Local-first AI** — no hosted LLM API, no managed vector database. Everything runs on the developer's machine.

---

## Technologies

**ML / Data:** Python 3.12, XGBoost, scikit-learn, SciPy, SHAP, pandas, NumPy, PyArrow
**Backend:** FastAPI, Pydantic v2, pydantic-settings, uvicorn
**AI Assistant:** Ollama, custom RAG pipeline
**Mobile:** Kotlin, Compose Multiplatform, Ktor, Koin, Material 3
**Tooling:** uv, Gradle, Ruff, Black, MyPy, Detekt, Spotless, GitHub Actions

---

## Engineering Practices

- **945 tests** — 872 Python (including 37 against the real trained model) and 73 Android (ViewModels written test-first).
- **Strict typing** — MyPy on the Python codebase; Kotlin with `val`-by-default and exhaustive `when`.
- **Conventional commits, ADRs and reports** — every structural decision is recorded; every experiment has a report with the command to reproduce it.
- **One concern per pull request**, self-reviewed against a written checklist.
- **CI on every pull request** — lint, format, types, tests and the Android build.

---

## Impact

A demonstration of full-stack AI engineering: data engineering discipline (validated, versioned, leakage-safe data), ML engineering (honest evaluation, model registry, promotion rules), AI product engineering (explainability and grounding as API contracts), backend engineering (versioned API, graceful degradation, daily refresh), and mobile engineering (MVVM, dependency injection, offline-first client), all in one coherent, tested system.

---

## Key Learnings

- More and better data beat model tuning by a wide margin.
- A result only counts once it survives a fair split, a strong benchmark and a confidence interval.
- Treating explainability and grounding as product features forces better engineering.
- Training/serving parity matters more than model choice.
