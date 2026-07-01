# Architecture Impact — Stages 1–7

How each stage built on the previous one, what capability it introduced, and what it enabled downstream.

---

## Overview

The Football Intelligence Platform was built incrementally over 7 stages. Each stage had a single, bounded concern. This document traces how the architecture evolved and why decisions made in early stages shaped what became possible later.

---

## Stage 1 — Repository Foundation

**New capability:** A structured, governed repository that any contributor can navigate without asking questions.

**Key decisions:**
- Clean Architecture layer model defined in `.claude/CLAUDE.md` before any code was written. All subsequent stages must respect this contract.
- Conventional commits enforced from the first commit. This makes the changelog generatable and the git history readable.
- ADR policy established before any ADRs were written. When Stage 7 made algorithm choices, the policy was already in place.

**Affected modules:** All of them — this stage set the rules every subsequent stage followed.

**Downstream impact:** The single `CLAUDE.md` file became the authoritative source of truth for all agents and contributors. Its existence meant that every subsequent stage could be implemented without renegotiating standards.

---

## Stage 2 — Compose Foundation

**New capability:** A buildable Android application shell with a defined module graph.

**Key decisions:**
- 13-module Gradle structure defined upfront (6 feature, 6 core, 1 app). Adding a new screen requires creating a feature module, not modifying existing ones.
- MVVM with `StateFlow` chosen over alternatives. All future ViewModels will follow this pattern.
- `core-testing` separated as a test-only dependency. It is never shipped in the APK.
- Spotless and Detekt configured. Code quality gates exist before any Kotlin code was written.

**Affected modules:** `frontend/` entirely.

**Downstream impact:** When the backend (Stage 9) and assistant (Stage 10) are built, the Android feature modules already know their interface. `feature-prediction` is a placeholder now; it becomes real when the backend API exists. The module boundaries cannot change without architectural justification.

---

## Stage 3 — AI Workspace

**New capability:** A typed, linted, tested Python workspace that can be extended without breaking the existing contract.

**Key decisions:**
- uv chosen over pip + venv. `uv.lock` pins every transitive dependency, making builds reproducible across machines.
- Pydantic v2 for all schemas. Type safety is enforced at the boundary between the ingestion layer and everything above it.
- Strict MyPy (`strict = true`). This catches incorrect assumptions early when the codebase is still small and easy to reason about.

**Affected modules:** `ai/schemas/`, `ai/shared/`, `ai/tests/`.

**Downstream impact:** When Stage 4 introduced three provider implementations, all three had to conform to the `ProcessedMatch` schema defined here. When Stage 6 produced the feature matrix, it could trust that the input schema was already validated. The schema defined in Stage 3 is the data contract that connects every stage from 4 to 7.

---

## Stage 4 — Data Acquisition Framework

**New capability:** A pluggable, testable mechanism for fetching football data from any provider.

**Key decisions:**
- `HttpTransport` protocol injected into `DatasetDownloader`. This meant tests could run offline with a `FakeTransport` from day one.
- Three providers implemented (football-data.co.uk, FBref, Understat) before any was used in production. This validated the abstraction's generality before committing to it.
- `DatasetStorage` owns path logic. Callers never construct paths — they receive `Path` objects back.
- `MetadataBuilder` mandated for every download. Provenance is not optional.

**Affected modules:** `ai/providers/`, `ai/ingestion/`, `ai/metadata/`.

**Downstream impact:** Stage 5 built `IngestionPipeline` on top of `DatasetDownloader`. Because the storage and path logic were already encapsulated, Stage 5 focused entirely on the canonical schema. The three-provider architecture meant that a second data source (FBref player stats) could be added in a future stage without touching the ingestion core.

---

## Stage 5 — Real Dataset Ingestion

**New capability:** A live, validated, versioned football dataset ready for modelling.

**Key decisions:**
- `IngestionPipeline` does not reuse `DatasetDownloader` — it re-implements the download flow to own the canonical output. This avoids coupling two independently useful classes.
- Separate `RawMatch` and `ProcessedMatch` schemas. The provider column names (`home_goals_ft`) and domain column names (`full_time_home_goals`) belong to different vocabularies.
- `MatchNormalizer` skips failing rows rather than aborting. 380 matches with 0 failures is the expected case; resilience against 1–2 bad rows is realistic.
- CLI entry point (`python -m scripts.ingest_football_data`) with argparse. Every pipeline step is CLI-invocable and scriptable.

**Affected modules:** `ai/schemas/`, `ai/ingestion/pipeline.py`, `ai/scripts/`.

**Downstream impact:** Stage 6 depended entirely on the `ProcessedMatch` CSV produced here. The schema separation meant that Stage 6's feature generators could reference domain column names (`full_time_home_goals`) without knowing anything about provider normalisation. The versioned file naming (`v<timestamp>`) meant that multiple ingestion runs co-existed safely.

---

## Stage 6 — Feature Engineering

**New capability:** 42 pre-match engineered features with no data leakage, ready for model training.

**Key decisions:**
- `BaseFeature` ABC with a single `compute(df) → df` contract. Each generator is independently testable and composable.
- `FeatureRegistry` with Kahn's topological sort. Features declare dependencies; the registry resolves order. Adding a new feature that depends on Elo requires only declaring `dependencies = ["EloRatingFeature"]`.
- `.shift(1)` on all rolling and expanding features. Row 0 per team always yields NaN — the mathematically correct behaviour for a team with no match history.
- Parquet output with pyarrow. Column dtypes are preserved exactly. No type inference or CSV ambiguity at training time.

**Affected modules:** `ai/feature_engineering/`, `datasets/features/`.

**Downstream impact:** Stage 7 loaded `feature_matrix.parquet` and filtered to the 42 pre-match feature columns. The `.shift(1)` guarantee meant the training pipeline could trust that no label-derived information was present in any feature. The `FeatureRegistry` design meant that Stage 8 (SHAP explainability) can retrieve the feature names and descriptions programmatically rather than hardcoding them.

---

## Stage 7 — Model Training & Evaluation

**New capability:** A trained, evaluated, versioned XGBoost model with full experiment tracking.

**Key decisions (see ADRs 001–003):**
- **ADR 001:** XGBoost over Logistic Regression, Random Forest, and Neural Networks. XGBoost handles mixed feature types, provides native feature importance, and converges faster on small tabular datasets.
- **ADR 002:** joblib serialisation bundles the classifier, imputer, and label encoder into a single file. `MatchPredictor.from_path()` loads a fully functional inference object with one call.
- **ADR 003:** Chronological 70/15/15 split rejects random splitting. A random split would allow future-season matches to appear in the training set, inflating accuracy estimates.
- `TimeSeriesSplit` for cross-validation. Standard k-fold would allow future-to-past leakage within the CV folds.
- Model card generated programmatically from the `EvaluationReport`. It cannot drift from actual metrics.
- `registry.json` records the git commit at training time. Every run is reproducible by checking out the exact commit and re-running the pipeline.

**Affected modules:** `ai/training/`, `ai/evaluation/`, `ai/inference/`, `ai/model_registry/`, `models/`.

**Downstream impact:**
- **Stage 8 (SHAP):** `model.joblib` contains the XGBClassifier. SHAP's `TreeExplainer` accepts XGBoost models directly. The feature names are available from `FeatureRegistry`.
- **Stage 9 (Backend):** `MatchPredictor.from_path()` is the inference interface the backend will call. No backend code needs to know about training or feature engineering.
- **Stage 12 (Evaluation):** The `EvaluationReport` schema and `registry.json` provide the baseline for structured evaluation across all stages.

---

## Architectural Invariants Established Across All Stages

| Invariant | Established in | Used by |
|---|---|---|
| Raw data is immutable | Stage 5 | All future ingestion runs |
| All schemas are Pydantic | Stage 3 | Stages 4–7 and all future stages |
| All pipeline steps are CLI-invocable | Stage 5 | Stages 6, 7 and CI |
| HttpTransport is injected | Stage 4 | All provider tests |
| `.shift(1)` on all rolling features | Stage 6 | Stage 7 training, Stage 8 SHAP |
| Chronological data splits | Stage 7 (ADR 003) | Stage 8, 9, 12 |
| Artifacts versioned by UTC timestamp | Stage 5 | Stages 6, 7 |
| Git commit recorded at training time | Stage 7 | Stage 9 (model serving), Stage 12 |
