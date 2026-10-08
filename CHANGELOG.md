# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- The assistant can call tools that run the prediction, SHAP explanation and fixtures services, so it quotes the served model's numbers instead of refusing match questions (#65, ADR 018).
- Season questions in the assistant: results, head-to-head and the next meeting (for example the next Manchester derby), and the league table on any date, with a goals-model projection of points, goals and clean sheets for dates still ahead. A rule-based router picks the tools and answers player and next-season questions without the model (#76, ADR 021).
- Tap a fixture on the home screen to open its prediction (#73).
- Team crests and league emblems next to names, via `/v2/teams/{team}/crest` and `/v2/competitions/{competition}/emblem` redirects, and a crest celebration for a predicted win (#74, ADR 020).
- Assistant evals: a grounding check that answers quote `/v2/predict` without invented numbers, and an abstention check for "I don't know" (#65, #66).
- Invite-only sign-in and consent for hosted deployments: invites, sessions, a consent notice, bans and `scripts.manage_accounts`. Off locally (`AUTH_REQUIRED`); on, it guards every `/v2` data route and drops `/v1` (#79, ADR 022).
- Android sign-in: a Sign in / Invite code screen under a green header, a consent notice after the first sign-in with an opt-in for storing question text, and Sign out in Settings. The app sends the session token on every request and returns to sign-in on a 401 (#84, ADR 022).

### Changed
- The default chat model is `qwen2.5:7b-instruct` instead of `llama3.2`, which misquoted tool numbers and failed both assistant evals (ADR 019).

### Fixed
- The assistant's relevance cut-off let every retrieved chunk through; it now drops chunks that don't match the question (#66).
- The likeliest-scores card explains why a draw can top it even when one side is the favourite (#75).
- The grounding eval no longer flags numbers the assistant repeats from the API's own error message.

---

## [2.1.0] — 2026-09-29

The API is unchanged and still reports version 2.0.0.

### Added
- Tactics Board adaptive app icon with a themed (monochrome) layer (#56, ADR 016).
- Kick-off launch screen: the ring fills in on Android 12+, a still ring on Android 8 to 11 (#56).
- Kick-off loading animation in place of every loading spinner, including pull to refresh (#56).

### Changed
- Every markdown file checked against the code and updated for v2; "Lessons Learned" removed from the README (#57, #58).
- Branch flow: work merges into `develop`; `main` only takes release pull requests and hotfixes, each tagged. CI runs on pull requests into both, and both branches are protected (#59).

[2.1.0]: https://github.com/SumukhaK/football-intelligence-platform/releases/tag/v2.1.0

---

## [2.0.1] — 2026-09-29

A patch release. The API is unchanged and still reports version 2.0.0.

### Fixed
- Offline mode falls back within seconds (#54). The app used to wait about 50 seconds before showing saved data under the offline banner. Connecting now gives up after 5 seconds, while a connected request still gets 30, so the banner appears after about 10 seconds on the emulator.

### Added
- Demo video (#53): a 3-minute narrated walk-through with English subtitles, linked from the README. Notes are in `docs/showcase/demo-video/`.
- Dated accuracy check (#52): the README's 2026/27 section now says when it was measured.

[2.0.1]: https://github.com/SumukhaK/football-intelligence-platform/releases/tag/v2.0.1

---

## [2.0.0] — 2026-09-29

A major version: the API contract changes and the model is replaced. `/v1` and the unversioned paths keep the v1.0.0 contract and the original Premier League model (ADR 014); `/v2` is current.

### Added
- Five leagues: Premier League, Bundesliga, La Liga, Serie A and Ligue 1, 2000/01 to 2025/26, 46,709 matches (ADR 005, ADR 006, ADR 012).
- Retrained model `20260928_123224` with a season-based split and walk-forward tuning (ADR 007): 52.45% accuracy and log loss 0.976 on the 2023/24 test season.
- Server-side match features: clients send two team names and the server builds all 42 features from match history (ADR 008).
- Plain-language explanations: every SHAP contribution has a fan-friendly label and value.
- Draw tag: predictions with a draw probability of at least 0.28 are tagged "draw possible"; the pick never changes (ADR 011).
- Dixon-Coles goals model per league with likely scores and goal markets through `POST /v2/insights` (ADR 009).
- Upcoming fixtures from openfootball through `GET /v2/fixtures` (ADR 015).
- Daily refresh of results and fixtures inside the backend, without a restart (ADR 013).
- Versioned API (`/v1` frozen, `/v2` current), new `GET /competitions` and `GET /teams`, and a rate limit of 120 requests a minute per client (ADR 014).
- App: Fixtures home with one tab per league, bottom navigation (Fixtures, Predict, Assistant, Settings), league picker, likely scores, offline cache with a banner, pull to refresh and plain-language errors.
- `ai/.env.example` listing every backend setting.

### Documentation
- ADRs 005 to 015.
- `docs/api.md` covering both API versions.
- `docs/releases/v2.0.0.md` — release notes.
- Reports on the multi-league retraining, the 2026/27 live check, draw handling, the goals model and the Kaggle extras experiment.

[2.0.0]: https://github.com/SumukhaK/football-intelligence-platform/releases/tag/v2.0.0

---

## [1.0.0] — 2026-07-01

### Added

#### Stage 11 — Compose Multiplatform Android Application
- 8-screen Android app: Home, Match Prediction, Prediction Result, Explain Prediction, AI Assistant Chat, Model Information, Settings, About.
- MVVM architecture: Composables in `commonMain`, ViewModels in `androidMain`, repositories returning `NetworkResult<T>`.
- Ktor 2.3.12 HTTP client covering all 5 backend endpoints.
- Koin 3.5.6 dependency injection; AndroidX Navigation Compose 2.8.3 routing.
- `FootballTheme` with Material 3 light/dark colour scheme.
- 9 repository unit tests across 4 feature modules (JUnit 5 + MockK).
- `buildNeutralFeatures()` providing 44 neutral values for demo predictions (documented limitation).

#### Stage 12 — End-to-End Integration & Production Readiness
- 36 integration tests in `ai/tests/integration/` covering all 5 API endpoints with real model artifacts.
- Prediction pipeline integration tests: model load, structured output, probability sanity, latency (<500 ms).
- Explainability pipeline integration tests: SHAP values finite, positive/negative attribution verification, latency (<3 s).
- API integration tests: health, model info, predict, explain, and assistant graceful-503 without Ollama.
- Error recovery tests: 503 on missing model, 422 on bad input, 404/405 on wrong routes.
- Full pytest suite: 462 tests passing (426 unit + 36 integration).
- Performance benchmarks documented: prediction <100 ms, explanation <2 s, health <50 ms.
- `docs/demo/stage-12-demo.md` — complete end-to-end demo guide with prerequisites, flows, and troubleshooting.
- `docs/reports/stage-12-summary.md` — production readiness assessment.
- `docs/releases/v1.0.0.md` — final release notes.
- `docs/releases/v1.0.0-readiness.md` — final release readiness report.

### Documentation
- `docs/reports/stage-11-summary.md` — Android application stage report.
- `docs/reports/stage-12-summary.md` — end-to-end integration stage report.
- `docs/demo/stage-11-demo.md` — Android application demo guide.
- `docs/demo/stage-12-demo.md` — end-to-end integration demo guide.
- Demo index updated to include Stages 11 and 12.
- Docs index updated to include Stages 11 and 12 reports, demos, and release.
- `CHANGELOG.md` updated with [1.0.0] entries for Stages 11–12.
- `docs/showcase/` — project showcase, timeline, portfolio summary, 50-question interview guide, demo scripts (5/10/20-minute), and screenshot capture checklist.
- README.md rewritten as a recruiter/contributor-facing project showcase: tagline, key capabilities, architecture diagrams for every pipeline, lessons learned, and an explicit out-of-scope section.

[1.0.0]: https://github.com/SumukhaK/football-intelligence-platform/releases/tag/v1.0.0

---

## [0.2.0] — 2026-06-30

### Added

#### Stage 8 — Explainable AI (SHAP)
- `explainability/` package: `SHAPExplainer`, `ExplainerCache`, `ExplainabilityPipeline`, `ExplanationService`.
- `shap.TreeExplainer` over the XGBoost booster with multi-class output normalisation to `(n_samples, n_features, n_classes)`.
- `ExplainerCache` — class-level dict keyed by model version; avoids rebuilding the explainer per request.
- `LocalExplanation` and `GlobalSummary` — frozen Pydantic models with predictions, probabilities, per-feature SHAP contributions, top-positive/negative features, and version metadata.
- Generated artifacts: `global_summary.json`, `local_explanations.json`, `summary_plot.png`, `feature_importance.png`, `waterfall/` (10 samples × 3 classes), `force/` (10 samples × 3 classes), `dependence/` (top 5 features).
- CLI: `uv run python -m explainability.pipeline` — runs on 380 matches, persists all artifacts to `ai/explanations/`.
- ADR 004: SHAP TreeExplainer chosen over XGBoost native importance, LIME, and Captum.
- 54 new tests across 8 modules (320 total at stage completion).

#### Stage 9 — FastAPI Backend
- FastAPI application at `ai/backend/` (shares the `ai/` uv workspace and venv).
- Endpoints: `GET /health`, `GET /model`, `POST /predict`, `POST /explain`.
- `pydantic-settings` config (`BackendSettings`) with `model_path` and `registry_path`.
- FastAPI lifespan loads `PredictionService` and `ExplanationService` once at startup into `app.state`.
- `Depends` dependency injection — no global state, no singletons.
- Structured exception handling: `ModelNotAvailableError` → 503, `FeatureMissingError` → 422, unexpected → 500.
- Request logging middleware recording method, path, status, and duration.
- OpenAPI schema auto-generated; Swagger UI at `/docs`, ReDoc at `/redoc`.
- 43 backend tests across 7 files (363 total at stage completion).
- Start command: `uv run uvicorn backend.app.main:app --reload`

#### Stage 10 — Football Intelligence Assistant
- `assistant/` package with 8 sub-packages: `ingestion`, `chunking`, `embeddings`, `retrieval`, `prompting`, `generation`, `services`, plus `pipeline.py` facade.
- `DocumentLoader` ingesting `.md` and `.json` knowledge files into `Document` objects.
- `TextChunker` splitting documents into overlapping chunks with stable SHA-1 IDs.
- `OllamaEmbedder` calling the Ollama embedding API (default: `nomic-embed-text`).
- `VectorStore` backed by numpy arrays, persisted to disk; cosine similarity retrieval.
- `OllamaGenerator` calling the Ollama chat API (default: `llama3.2`).
- `AssistantService` orchestrating embed → retrieve → prompt → generate pipeline.
- System prompt instructs the assistant to answer only from retrieved context, cite sources as `[source: <filename>]`, and admit when it lacks information.
- Low-relevance chunks (< 0.50 cosine similarity) filtered before context assembly.
- `AssistantPipeline` facade: `build_index()`, `load_index()`, `query()` — CLI-runnable with `--rebuild` flag.
- Backend integration: `POST /assistant/chat` endpoint, `ChatService` adapter, `AssistantNotAvailableError` → 503, graceful startup when Ollama is absent.
- `assistant_available` field on `/health` response.
- 52 new assistant + backend tests; all Ollama calls mocked (426 total passing).
- Index build command: `uv run python -m assistant.pipeline --rebuild`

### Documentation
- `docs/reports/stage-08-summary.md` — SHAP explainability stage report.
- `docs/reports/stage-09-summary.md` — FastAPI backend stage report.
- `docs/reports/stage-10-summary.md` — Football intelligence assistant stage report.
- `docs/demo/stage-08-demo.md` — SHAP explainability demo guide.
- `docs/demo/stage-09-demo.md` — FastAPI backend demo guide.
- `docs/demo/stage-10-demo.md` — AI assistant demo guide.
- `docs/adr/004-shap-for-explainability.md` — ADR for SHAP selection.
- `docs/releases/v0.2.0.md` — Release notes.
- `docs/releases/v0.2.0-readiness.md` — Release readiness report.
- README Mermaid diagram updated to show completed Stages 8–10 and planned Stage 11.
- ADR index updated to include ADR 004.

[0.2.0]: https://github.com/SumukhaK/football-intelligence-platform/releases/tag/v0.2.0

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
- Compose Multiplatform Android-first Gradle project with 14 modules (`app`, 7 core, 6 feature).
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
