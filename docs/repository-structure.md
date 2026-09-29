# Repository Structure

A reference guide to every top-level directory: what it owns, what belongs there, and what does not.

---

## Root

```
football-intelligence-platform/
├── .claude/
├── .github/
├── ai/
├── backend/
├── datasets/
├── docs/
├── frontend/
├── infrastructure/
├── playbook/
├── scripts/
├── tools/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE
└── README.md
```

---

## `.claude/`

**Purpose:** Claude Code project context.

**Owns:**
- `CLAUDE.md` — the single authoritative source of project standards, architecture rules, coding conventions, and AI agent instructions.

**Does not own:** general project documentation (that belongs in `docs/`).

---

## `.github/`

**Purpose:** GitHub-specific configuration.

**Owns:**
- `workflows/` — GitHub Actions CI definitions.
- `ISSUE_TEMPLATE/` — structured issue templates (bug report, task, ADR request).
- `PULL_REQUEST_TEMPLATE.md` — standard PR description template.
- `CODEOWNERS` — code ownership assignments.

**Does not own:** deployment scripts (those belong in `scripts/`) or infrastructure config (that belongs in `infrastructure/`, which is an empty placeholder today).

---

## `ai/`

**Purpose:** The standalone Python AI workspace. Owns the complete data-to-model pipeline, the assistant and the FastAPI backend.

**Owns:**
- `config/` — `pydantic-settings`-based configuration and path layout.
- `shared/` — common types, exceptions, and constants used across all packages.
- `providers/` — data provider adapters: `football-data.co.uk`, FBref, Understat.
- `ingestion/` — HTTP downloader, storage orchestration, `IngestionPipeline`.
- `validation/` — DataFrame-level quality rules and schema compatibility checks.
- `preprocessing/` — cleans and normalises validated data into `datasets/processed/`.
- `schemas/` — Pydantic schema definitions for all datasets (`RawMatch`, `ProcessedMatch`).
- `metadata/` — `DatasetMetadata` model and `MetadataBuilder`.
- `feature_engineering/` — 9 composable feature generators, `FeatureRegistry`, `FeaturePipeline`.
- `training/` — `TrainingConfig`, chronological and season splitters (ADR 007), hyperparameter tuning, XGBoost trainer, persistence, registry and model cards.
- `evaluation/` — metrics, cross-validation, plots, model comparison, draw analysis, in-season and goals-model evaluation.
- `inference/` — `MatchPredictor`: loads a persisted model and returns `MatchPrediction`.
- `explainability/` — SHAP explainer, plain-language feature labels, explanation pipeline and plots.
- `goals/` — Dixon-Coles goals model, score grid and goal-market insights (ADR 009).
- `assistant/` — the retrieval-grounded assistant: chunking, embeddings, vector store, retrieval, prompt templates (`assistant/prompting/templates.py`) and generation.
- `model_registry/` — JSON-backed local model registry with versioned `ModelEntry` records.
- `backend/` — the FastAPI application in `backend/app/`: `routers/`, `services/`, `schemas/`, `middleware/` (rate limiter) and `exceptions/`.
- `scripts/` — operational CLI scripts: `backfill_football_data`, `ingest_football_data`, `refresh_live_dataset`, `refresh_fixtures`, and two experiment scripts (`draw_feature_experiment`, `kaggle_extras_experiment`).
- `models/` — trained model output (runs, `latest/`, `registry.json`). Gitignored: only `.gitkeep` is tracked. See `ai/models/` below.
- `explanations/` — SHAP explanation output. Gitignored.
- `datasets/` — where the pipelines read and write by default when run from `ai/` without explicit paths (the README Quick Start passes `../datasets` instead). Only `.gitkeep` is tracked; the shared data lives in the root `datasets/`.
- `rag/`, `prompts/` — empty placeholders (`.gitkeep` only). The assistant code lives in `assistant/`.
- `tests/` — unit, backend and integration tests mirroring the source package structure.
- `pyproject.toml` — package metadata, dependencies, toolchain configuration.
- `uv.lock` — pinned dependency lockfile.

**Does not own:** the shared raw, processed and feature datasets (those live in the root `datasets/`).

---

## `backend/`

**Purpose:** Placeholder. It holds a `README.md` (and `.gitkeep`) that describes the API and points to the code.

The FastAPI code lives in `ai/backend/app/` so it can import the model, feature and assistant packages directly. API routes are in `ai/backend/app/routers/`, and backend tests are in `ai/tests/backend/`.

---

## `datasets/`

**Purpose:** All football data, raw and processed. Raw data is immutable.

**Owns:**
- `raw/` — immutable source data exactly as received from providers. Never overwrite; version by timestamp.
- `processed/` — canonical `ProcessedMatch` CSVs produced by the ingestion pipeline.
- `features/` — the feature matrix (`feature_matrix.parquet`) and feature metadata produced by the feature engineering pipeline. `features/top5/` holds the five-league features the current model uses; the files directly in `features/` are the original single-season Premier League features.
- `schemas/` — reviewed reference tables such as `team_aliases.csv` (ADR 006).

Only metadata and reports are tracked. CSV and Parquet data files are gitignored and generated locally.

**Does not own:** trained model artifacts (those live in `ai/models/`), or code (that belongs in `ai/`).

**Invariants:**
- Files in `raw/` are never overwritten. New runs write new versioned files.
- Every dataset in `processed/` or `features/` has a corresponding metadata sidecar.
- Files that contain secrets or PII must never enter this directory.

---

## `docs/`

**Purpose:** All project documentation that is not code-adjacent.

**Owns:**
- `adr/` — Architectural Decision Records. One file per decision, numbered sequentially.
- `reports/` — stage completion summaries with executive summary, design decisions, tests, and metrics.
- `releases/` — release notes and readiness reports.
- `plans/` — plans for the multi-league work and the next phase.
- `setup/` — installation and quick-start guides.
- `reference/` — CLI command reference.
- `api.md` — the full API contract for both versions.
- `showcase/` — project write-up, portfolio summary, interview guide, demo video notes and screenshots.
- `demo/` — demo scripts for each completed stage, aimed at technical interviewers.
- `README.md` — documentation index.

A few other folders (`ai/`, `architecture/`, `backend/` and similar) are empty placeholders.

**Does not own:** code examples that belong alongside the source (use inline docstrings), or ephemeral notes (use issues).

---

## `frontend/`

**Purpose:** Compose Multiplatform Android-first application.

**Owns:**
- `app/` — application entry point, dependency injection, root `NavHost`.
- `feature-*/` — screen-level feature modules (one module per screen area).
- `core-*/` — shared infrastructure and UI modules.
- `build-logic/` — shared Gradle convention plugins.
- `gradle/` — Gradle wrapper and version catalog.

**Modules:** 14 Gradle modules: `app`, 7 core modules and 6 feature modules (see `settings.gradle.kts`).

**Module graph:** Feature modules depend on core modules. Feature modules never depend on each other. `app` depends on the four features in use (home, prediction, assistant, settings); `feature-match` and `feature-team` are empty and not wired in.

**Does not own:** business logic (that belongs in domain/service classes), network configuration beyond Ktor setup (that belongs in `core-network`), or ML inference (that belongs in `ai/` and is exposed through the API in `ai/backend/`).

---

## `ai/models/`

**Purpose:** Persisted model artifacts, written by the training pipeline when it runs from `ai/`. The whole folder is gitignored except `.gitkeep`, so every artifact is generated locally.

**Owns:**
- `runs/<timestamp>/` — per-run artifacts: `model.joblib`, `config.json`, `metrics.json`, `evaluation_report.json`, `model_card.md`, `plots/`.
- `latest/` — copy of the most recent successful run's artifacts. Always reflects the current best model.
- `evaluation/` — global evaluation report updated on every training run.
- `registry.json` — JSON model registry listing all trained versions with git commit, metrics, and framework versions.

**Does not own:** training code (that belongs in `ai/training/`), raw data (that belongs in `datasets/`).

**Gitignore policy:** nothing in this folder is tracked apart from `.gitkeep`. See `.gitignore` for the exact rules.

---

## `playbook/`

**Purpose:** Reserved for prompt templates and retrieval configurations.

Today it holds only a `README.md` and empty `stage-*/` and `templates/` folders (`.gitkeep`). The assistant's prompt templates live in code at `ai/assistant/prompting/templates.py`.

**Invariant:** Prompt templates are version-controlled and tested like code. They are never edited ad hoc.

---

## `infrastructure/`

**Purpose:** Empty placeholder (`.gitkeep` only) for future deployment configuration.

---

## `scripts/`

**Purpose:** Repository-level automation scripts that are not part of any application.

**Owns:** setup scripts, migration scripts, and CI helper scripts that operate on the repository as a whole.

**Does not own:** AI pipeline CLI scripts (those belong in `ai/scripts/`) or build logic (that belongs in `frontend/build-logic/`).

---

## `tools/`

**Purpose:** Shared CLI utilities that span multiple workspaces.

**Does not own:** workspace-specific scripts.

---

## Summary Table

| Directory | Language | Managed by | Primary concern |
|---|---|---|---|
| `.claude/` | Markdown | Manual | AI agent context |
| `.github/` | YAML | Manual | CI and GitHub config |
| `ai/` | Python 3.12 | uv | Data pipeline, ML training, evaluation, assistant, FastAPI backend |
| `backend/` | Markdown | Manual | Placeholder README; the code is in `ai/backend/` |
| `datasets/` | CSV, Parquet, JSON | Pipeline scripts | Raw and processed football data |
| `docs/` | Markdown | Manual | All project documentation |
| `frontend/` | Kotlin | Gradle | Compose Multiplatform Android app |
| `ai/models/` | JSON, joblib | Training pipeline | Trained model artifacts and registry (gitignored) |
| `infrastructure/` | — | — | Empty placeholder |
| `playbook/` | Markdown | Manual | Placeholder for prompt templates |
| `scripts/` | Shell, Python | Manual | Repository automation |
| `tools/` | Any | Manual | Shared CLI utilities |
