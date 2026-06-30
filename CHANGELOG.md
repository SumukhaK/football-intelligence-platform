# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] — 2026-06-30

### Added

#### Stage 1 — Repository Foundation
- Repository directory structure, root configuration files, and `.gitignore`.
- GitHub issue templates (bug report, task, ADR request), PR template, and CODEOWNERS.
- CI workflow skeleton with GitHub Actions.
- Project instructions in `.claude/CLAUDE.md`.
- Documentation hierarchy under `docs/` including ADR policy and index.
- Playbook structure under `playbook/` for prompt templates.
- AI workspace and dataset directory skeletons.

#### Stage 2 — Compose Foundation
- Compose Multiplatform Android-first Gradle project with 13 modules.
- Feature modules: `feature-home`, `feature-prediction`, `feature-match`, `feature-team`, `feature-assistant`, `feature-settings`.
- Core modules: `core-ui`, `core-design-system`, `core-navigation`, `core-model`, `core-network`, `core-common`, `core-testing`.
- MVVM architecture with sealed `UiState` classes and `StateFlow`-backed ViewModels.
- Material 3 design system tokens and theme.
- Ktor HTTP client configured in `core-network`.
- Spotless formatting and Detekt static analysis.

#### Stage 3 — AI Workspace
- Standalone Python 3.12 project under `ai/` managed with uv.
- Pydantic match schema (`schemas/match.py`) with 40+ validated fields.
- Schema validation test suite.
- Shared `exceptions.py` and `types.py` modules.
- Black, Ruff, MyPy, and pytest toolchain configured in `pyproject.toml`.

#### Stage 4 — Data Acquisition Framework
- `DatasetDownloader` orchestrating HTTP fetch → parse → normalise → validate → store.
- `HttpTransport` protocol with injectable `FakeTransport` for offline testing.
- Three provider implementations: `FootballDataProvider`, `FBrefProvider`, `UnderstatProvider`.
- `DatasetStorage` for raw bytes, Parquet DataFrames, and metadata JSON.
- `MetadataBuilder` producing `DatasetMetadata` with source provenance and version tags.
- 104 tests covering all providers, storage, and pipeline orchestration.

#### Stage 5 — Real Dataset Ingestion
- Premier League 2023/24 ingested from football-data.co.uk: 380 matches.
- Schema validation enforcing 9 completeness and quality rules via `DatasetValidator`.
- Versioned raw Parquet storage at `datasets/raw/`.
- `DatasetMetadata` with column counts, row counts, and source URL.
- CLI script `scripts/ingest_football_data.py` for pipeline execution.

#### Stage 6 — Feature Engineering
- `FeatureRegistry` with 9 registered composable feature generators.
- Features: `RollingFormFeature`, `GoalStatisticsFeature`, `HomeAdvantageFeature`, `AwayFormFeature`, `RestDaysFeature`, `HeadToHeadFeature`, `LeaguePositionFeature`, `EloRatingFeature`, `StrengthOfScheduleFeature`.
- `FeatureEngineeringPipeline` producing a 42-column feature matrix.
- Feature matrix saved as `datasets/features/feature_matrix.parquet`.
- `FeatureMetadata` with per-feature descriptions and generation report.
- 142 tests across all feature generators, pipeline, and registry.

#### Stage 7 — Model Training & Evaluation
- XGBoost multi-class classifier (`multi:softprob`) for Home/Draw/Away prediction.
- Chronological 70/15/15 train/validation/test split (`TrainValTestSplitter`).
- Early stopping on validation log loss.
- `TimeSeriesSplit` cross-validation (5 folds) via `CrossValidator`.
- Evaluation metrics: accuracy, F1 weighted, log loss, ROC AUC OvR.
- Training run artifacts persisted to `models/runs/<timestamp>/`.
- `models/latest/` symlinked to the most recent successful run.
- Auto-generated `model_card.md` for every training run.
- JSON-backed `ModelRegistry` with git commit traceability and framework version pinning.
- Evaluation report at `models/evaluation/evaluation_report.json`.
- `MatchPredictor` inference wrapper loading model and returning `MatchPrediction`.
- 3 ADRs accepted: XGBoost choice, joblib serialisation, chronological split.
- 48 new tests; 266 total tests passing.

[0.1.0]: https://github.com/SumukhaK/football-intelligence-platform/releases/tag/v0.1.0
