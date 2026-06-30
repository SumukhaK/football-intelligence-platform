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
├── models/
├── playbook/
├── scripts/
├── tools/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
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

**Does not own:** deployment scripts (those belong in `scripts/`) or infrastructure config (that belongs in the future `infrastructure/` directory).

---

## `ai/`

**Purpose:** The standalone Python AI workspace. Owns the complete data-to-model pipeline.

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
- `training/` — `TrainingConfig`, chronological splitter, XGBoost trainer, persistence, registry.
- `evaluation/` — metrics, cross-validation, Matplotlib plots, Pydantic report models.
- `inference/` — `MatchPredictor`: loads a persisted model and returns `MatchPrediction`.
- `model_registry/` — JSON-backed local model registry with versioned `ModelEntry` records.
- `scripts/` — operational CLI scripts (`ingest_football_data.py`).
- `tests/` — unit tests mirroring the source package structure.
- `pyproject.toml` — package metadata, dependencies, toolchain configuration.
- `uv.lock` — pinned dependency lockfile.

**Future (planned):**
- `rag/` — retrieval pipeline: indexing, search, context assembly (Stage 10).
- `prompts/` — prompt templates mirroring `playbook/` (Stage 10).

**Does not own:** raw or processed datasets (those live in `datasets/`), trained model artifacts (those live in `models/`), or API routes (those belong in `backend/`).

---

## `backend/`

**Purpose:** FastAPI application and domain logic. (Planned — Stage 9.)

**Will own:**
- `routers/` — one router per domain area.
- `services/` — business logic service classes.
- `domain/` — entities, value objects, business rules.
- `infrastructure/` — database access, ML model loading.
- `tests/` — unit and integration tests.

**Does not own:** ML training logic (that belongs in `ai/`), or Android UI (that belongs in `frontend/`).

---

## `datasets/`

**Purpose:** All football data, raw and processed. Raw data is immutable.

**Owns:**
- `raw/` — immutable source data exactly as received from providers. Never overwrite; version by timestamp.
- `processed/` — canonical `ProcessedMatch` CSVs produced by the ingestion pipeline.
- `features/` — the feature matrix (`feature_matrix.parquet`) and feature metadata produced by the feature engineering pipeline.
- `schemas/` — JSON Schema or Pydantic definitions for dataset contracts (supplements `ai/schemas/`).

**Does not own:** trained model artifacts (those live in `models/`), or code (that belongs in `ai/`).

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
- `setup/` — installation and quick-start guides.
- `reference/` — CLI command references and API specifications.
- `demo/` — demo scripts for each completed stage, aimed at technical interviewers.
- `README.md` — documentation index.

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

**Module graph:** Feature modules depend on core modules. Feature modules never depend on each other. `app` depends on all features.

**Does not own:** business logic (that belongs in domain/service classes), network configuration beyond Ktor setup (that belongs in `core-network`), or ML inference (that belongs in `ai/` and exposed via `backend/`).

---

## `models/`

**Purpose:** Persisted model artifacts. Git-tracked metadata; large binaries are gitignored.

**Owns:**
- `runs/<timestamp>/` — per-run artifacts: `model.joblib`, `config.json`, `metrics.json`, `evaluation_report.json`, `model_card.md`, `plots/`.
- `latest/` — copy of the most recent successful run's artifacts. Always reflects the current best model.
- `evaluation/` — global evaluation report updated on every training run.
- `registry.json` — JSON model registry listing all trained versions with git commit, metrics, and framework versions.

**Does not own:** training code (that belongs in `ai/training/`), raw data (that belongs in `datasets/`).

**Gitignore policy:** `model.joblib` and other large binary files are gitignored. The registry, model card, config, and metrics JSON files are tracked. See `.gitignore` for the exact policy.

---

## `playbook/`

**Purpose:** Prompt templates and retrieval configurations. (Partially planned — Stage 10.)

**Will own:**
- Versioned prompt templates for the football intelligence assistant.
- Retrieval configuration files.
- Prompt evaluation results.

**Invariant:** Prompt templates are version-controlled and tested like code. They are never edited ad hoc.

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
| `ai/` | Python 3.12 | uv | Data pipeline, ML training, evaluation |
| `backend/` | Python 3.12 | uv (planned) | FastAPI REST API |
| `datasets/` | CSV, Parquet, JSON | Pipeline scripts | Raw and processed football data |
| `docs/` | Markdown | Manual | All project documentation |
| `frontend/` | Kotlin | Gradle | Compose Multiplatform Android app |
| `models/` | JSON, joblib | Training pipeline | Trained model artifacts and registry |
| `playbook/` | Markdown, JSON | Manual | Prompt templates and retrieval config |
| `scripts/` | Shell, Python | Manual | Repository automation |
| `tools/` | Any | Manual | Shared CLI utilities |
