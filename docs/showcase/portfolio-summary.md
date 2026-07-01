# Portfolio Summary — Football Intelligence Platform

*A two-page summary for recruiters and hiring managers.*

---

## Project Overview

The Football Intelligence Platform is a complete, working AI system that predicts Premier League match outcomes, explains every prediction, answers natural-language questions grounded in its own data, and serves all of this through a native Android app — built end-to-end by one engineer in 12 sequential stages.

It is not a notebook or a prototype. It is a tested (462 passing tests), documented, reproducible system that runs entirely on a laptop with zero cloud dependency: a Python ML pipeline, a FastAPI backend, a local RAG assistant powered by Ollama, and a Compose Multiplatform Android client.

**The goal was never "build a model." It was "ship a model as a trustworthy, explainable, usable product."**

---

## Technical Challenges

| Challenge | Solution |
|---|---|
| Time-series leakage in rolling-window features | Applied `.shift(1)` to every rolling feature and enforced a chronological (not random) train/val/test split |
| Making explainability fast enough for per-request API use | Built `ExplainerCache` to avoid rebuilding SHAP's `TreeExplainer` on every call; resulting latency ~7 ms |
| Preventing LLM hallucination without fine-tuning | Enforced source-only answering via system prompt + relevance-filtered retrieval, with tested graceful degradation when the LLM is unavailable |
| Sharing state across a multi-screen mobile flow | Used Android Navigation's back-stack entry scoping to share one `ViewModel` across Prediction → Result → Explain |
| Validating the system without mocking away the hard parts | Wrote a 36-test integration suite that runs against the *real* trained model, not mocks — catching numerical and latency issues mocked tests cannot |

---

## Architecture Decisions

Four decisions were significant enough to be formally recorded as ADRs:

1. **XGBoost** for prediction — strong tabular baseline with native SHAP `TreeExplainer` support.
2. **joblib** for model serialisation — simpler than ONNX for a single-model deployment, safer than raw pickle.
3. **Chronological train/val/test split** — required correctness for a time-ordered sports dataset; a random split silently leaks future information.
4. **SHAP `TreeExplainer`** over LIME/Captum — exact (not sampled) attribution, fast enough for live API use.

Beyond the ADRs: Clean Architecture with strict one-directional dependencies across both the Python backend and the Kotlin/Compose frontend; MVVM with `StateFlow` on Android; lifespan-based dependency injection in FastAPI (no global state, no per-request reloads).

---

## AI Components

- **XGBoost classifier** — `multi:softprob`, 42 engineered features, chronological CV, 56.1% test accuracy (33.3% random baseline), 0.625 ROC AUC.
- **SHAP explainability** — per-prediction, per-class feature attribution exposed through `POST /explain`, not buried in a notebook.
- **Retrieval-Augmented Generation** — Ollama embeddings (`nomic-embed-text`) into a numpy vector store, cosine retrieval, relevance filtering, and a source-constrained system prompt feeding `llama3.2`.
- **Local-first AI** — no hosted LLM API, no managed vector database. Everything runs on the developer's machine.

---

## Technologies

**ML / Data:** Python 3.12, XGBoost, scikit-learn, SHAP, pandas, NumPy, PyArrow
**Backend:** FastAPI, Pydantic v2, uvicorn
**AI Assistant:** Ollama, custom RAG pipeline
**Mobile:** Kotlin, Compose Multiplatform, Ktor, Koin, Material 3
**Tooling:** uv, Gradle, Ruff, Black, MyPy, Detekt, Spotless, GitHub Actions

---

## Engineering Practices

- **462 tests passing** across unit and integration suites; 426 mocked-contract tests plus 36 tests against the real trained model.
- **Strict typing** — MyPy `strict = true` on the entire Python codebase; Kotlin with `val`-by-default and exhaustive `when`.
- **Conventional commits, ADRs, and per-stage documentation** — every structural decision is recorded; every stage has a report and a demo guide.
- **One feature per pull request**, self-reviewed against a written checklist before requesting review.
- **CI on every push** — lint, format check, type check, full test suite.

---

## Impact

A demonstration of full-stack AI engineering capability: data engineering discipline (leakage-safe features, versioned datasets), ML engineering (reproducible training, model registry, evaluation), AI product engineering (explainability and grounding as API contracts, not afterthoughts), backend engineering (clean service architecture, structured error handling), and mobile engineering (MVVM, dependency injection, real API integration) — all in one coherent, tested system.

---

## Key Learnings

- Time-series leakage is easy to introduce and easy to miss without deliberate validation — chronological splitting should be the default assumption for sequential data, not an afterthought.
- Treating explainability and grounding as *product features with latency budgets* (not analysis scripts) forces better engineering and produces something users can actually rely on.
- Mocked tests validate contracts; tests against the real artifact validate correctness. A mature test suite needs both, and conflating them hides real bugs.
