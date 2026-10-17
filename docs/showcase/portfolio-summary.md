# Portfolio Summary — Football Intelligence Platform

*A two-page summary for recruiters and hiring managers.*

---

## Project Overview

The Football Intelligence Platform is a complete, working AI system for Europe's top five football leagues. It predicts match outcomes, offers SHAP explanations in plain football language, estimates likely scores, lists upcoming fixtures, answers natural-language questions grounded in its own documents and data (including league tables, results and season projections), and serves all of this through a native Android app. One engineer built it end to end: 12 stages up to v1.0.0, then the v2 releases.

It is not a notebook or a prototype. It is a tested (1,580 tests), documented, reproducible system that runs entirely on a laptop with no cloud dependency, and has an invite-only staging deployment recorded in the [hosting tracker](../plans/hosting-execution-tracker.md): a Python ML pipeline, a versioned FastAPI backend with structured logs and traces, a RAG assistant on Ollama locally or Cloudflare Workers AI when hosted, a container image for Cloud Run, and a Compose Multiplatform Android client. A [2-minute demo video](demo-video/README.md) shows it end to end.

**The goal was never "build a model." It was "ship a model as a trustworthy, explainable, usable product."**

---

## Technical Challenges

| Challenge | Solution |
|---|---|
| Time-series leakage in rolling-window features | `.shift(1)` on every rolling feature and a whole-season train/validation/test split with holdout seasons |
| Knowing whether a better score is real | Benchmarked against bookmaker odds, and used paired bootstrap intervals when comparing frozen-split candidates; serving refits use a separate dated backtest |
| Training/serving skew | The server builds all 42 features from match history with the training pipeline; clients send only team names |
| Draws the model never picks | Showed the draw probability is calibrated but flat, and retained a `draw_possible` API field instead of forcing picks; the current app shows the probabilities |
| Reducing unsupported answers without fine-tuning | Source-constrained prompts, retrieval, live tools, numeric checks and abstention evals; sources are logged, and these checks do not prove general faithfulness |
| Keeping old clients working after a breaking change | Path-versioned API: `/v1` keeps the v1.0.0 contract and model, `/v2` serves five leagues |
| A mobile app that stays useful offline | A caching decorator replays supported saved data responses with an offline banner; server errors are still shown |

---

## Architecture Decisions

Thirty-four ADRs record every structural decision (`docs/adr/`). The most important:

1. **XGBoost** for prediction — strong tabular baseline with exact SHAP `TreeExplainer` support.
2. **Five leagues, 26 seasons** — data mattered far more than tuning.
3. **Season-based split and evaluation** — the realistic way to test a time-ordered sports model.
4. **Server-side features** — one code path for training and serving.
5. **Dixon-Coles goals model** for likely scores, **draw tag** for tight games.
6. **Daily in-process refresh, API versions and a rate limiter** — fresh data, stable contracts, protection from runaway clients.
7. **Assistant tools and a rule-based router** — match and season answers quote the API's own services, not the model's guesses.

Beyond the ADRs: Clean Architecture with one-directional dependencies in both the Python backend and the Kotlin frontend; MVVM with `StateFlow` on Android; lifespan-based dependency injection in FastAPI.

---

## AI Components

- **XGBoost classifier** — `multi:softprob`, 42 pre-match features, 46,709 matches, tuned by season walk-forward CV. Test 2023/24: 52.5% accuracy and log loss 0.976 (random 33.3%; bookmakers 55.0% and 0.955). On 250 matches through 20 September 2026, the serving refit scored 52.0%, the frozen reporting model 52.4% and Bet365 51.6%; paired intervals include zero, so no superiority is established.
- **SHAP explainability** — per-prediction attribution through `POST /v2/explain`, with fan-friendly labels for every feature.
- **Dixon-Coles goals model** — likely scores, expected goals and goal markets through `POST /v2/insights`, refitted at startup and after enabled local refresh; the hosted container serves a snapshot.
- **Retrieval-Augmented Generation** — Ollama embeddings (`nomic-embed-text`) into a numpy vector store, cosine retrieval, and a source-constrained system prompt feeding `qwen2.5:7b-instruct`, which can also call the prediction, SHAP and fixtures services as tools. A rule-based router sends season questions (tables on any date, results, the next derby) to season tools, with a goals-model projection for future dates.
- **Local-first, hosting-ready AI** — everything runs on the developer's machine, with no managed vector database. For hosting, one setting swaps Ollama for Cloudflare Workers AI; the hosted model was chosen by the same two evals (ADR 025).
- **Observability and operations** — a versioned telemetry contract, request IDs, JSON logs, OpenTelemetry traces across retrieval, tool calls and generation, retries with backoff, and metrics and alerts kept as code (ADR 024).

---

## Technologies

**ML / Data:** Python 3.12, XGBoost, scikit-learn, SciPy, SHAP, pandas, NumPy, PyArrow
**Backend:** FastAPI, Pydantic v2, pydantic-settings, uvicorn, OpenTelemetry
**Hosting:** Docker, Google Cloud Run, Firestore, Secret Manager, Cloud Logging, Trace and Monitoring
**AI Assistant:** Ollama locally, Cloudflare Workers AI hosted, custom RAG pipeline
**Mobile:** Kotlin, Compose Multiplatform, Ktor, Koin, Material 3
**Tooling:** uv, Gradle, Ruff, Black, MyPy, Detekt, Spotless, ShellCheck, pip-audit, OSV-Scanner, GitHub Actions

---

## Engineering Practices

- **v2.6.0 release test totals: 1,580** — 1,373 Python (37 marked integration, including real-model flows and a live download) and 207 Android (ViewModels written test-first).
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
