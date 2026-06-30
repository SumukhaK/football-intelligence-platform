# Football Intelligence Platform

An AI-first football analytics application demonstrating practical AI engineering through structured data pipelines, machine learning, explainable predictions, and a grounded football intelligence assistant.

---

## Project Overview

The Football Intelligence Platform ingests structured football match and player data, trains an XGBoost model to predict match outcomes with SHAP-driven explanations, and surfaces those insights through a retrieval-augmented AI assistant and a Compose Multiplatform Android client.

This project is built to demonstrate AI engineering discipline: grounded responses, interpretable models, evaluated pipelines, and maintainable code.

---

## Vision

Build a system that is honest about what it knows, traceable in its reasoning, and maintainable by a single engineer without cloud infrastructure.

---

## Goals

- Ingest and process structured football data into a validated, queryable dataset.
- Train an XGBoost model to predict match outcomes with SHAP explanations on every prediction.
- Build a football intelligence assistant using Ollama, prompt engineering, and retrieval-augmented generation.
- Expose predictions and assistant capabilities through a FastAPI backend.
- Deliver a Compose Multiplatform Android-first frontend with TDD-verified ViewModels.
- Demonstrate structured AI evaluation: retrieval precision, answer faithfulness, hallucination rate.

---

## Repository Layout

```
.github/            # GitHub workflows, issue templates, PR template, CODEOWNERS
.claude/            # Claude Code project context and instructions
docs/               # Architecture docs, ADRs, design decisions, roadmap
playbook/           # Prompt templates, agent playbooks, retrieval configs
frontend/           # Compose Multiplatform Android application
backend/            # FastAPI application, domain logic, service layer
ai/                 # Data ingestion, feature engineering, model training, RAG, evaluation
datasets/           # Raw, interim, processed, and external football data
scripts/            # Setup, automation, and migration scripts
tools/              # Shared CLI utilities
infrastructure/     # Infrastructure configuration (future)
```

---

## Architecture Overview

The system follows Clean Architecture with strict layer separation.

| Layer | Responsibility |
|---|---|
| Domain | Entities, value objects, business rules |
| Application | Use cases, service interfaces, DTOs |
| Infrastructure | Database, external APIs, file I/O, ML models |
| Presentation | FastAPI routes, Compose UI, ViewModels |

Dependencies flow inward. Outer layers depend on inner layers. Inner layers know nothing of the outer world.

The frontend uses MVVM. ViewModels own state as `StateFlow`. Composables are stateless.

The AI layer is separate from the backend. The backend exposes AI results via API; it does not run models directly.

---

## System Data Flow

```mermaid
flowchart TD
    A["⚽ Football Data Sources\nfootball-data.co.uk · FBref · Understat"] --> B

    subgraph AI["AI Workspace (ai/)"]
        B["Ingestion Pipeline\nDatasetDownloader · IngestionPipeline\nschema validation · versioned storage"] --> C
        C["Canonical Dataset\ndatasets/processed/\nProcessedMatch · 380 matches"] --> D
        D["Feature Engineering\n9 feature generators · FeatureRegistry\nKahn topology sort · leakage prevention"] --> E
        E["Feature Matrix\ndatasets/features/feature_matrix.parquet\n42 pre-match features · 380 rows"] --> F
        F["Model Training\nXGBoost · chronological 70/15/15 split\nearly stopping · TimeSeriesSplit CV"] --> G
        G["Evaluation\naccuracy · F1 · log-loss · ROC AUC\nper-split + cross-validation"] --> H
        H["Model Registry\nmodels/registry.json\ngit commit traceability"]
        F --> I["Model Artifacts\nmodels/latest/model.joblib\nmodel_card.md · plots"]
    end

        I --> J["Explainability — Stage 8\nSHAP TreeExplainer · ExplanationService\nlocal + global artifacts"]
        J --> K["Backend API — Stage 9\nFastAPI · /predict · /explain\nOpenAPI · 43 tests"]
        K --> L["AI Assistant — Stage 10\nOllama · RAG · numpy vector store\nPOST /assistant/chat · 426 tests"]
    end

    subgraph FUTURE["Planned Stages"]
        M["Android App — Stage 11\nCompose Multiplatform · MVVM"]
    end

    L --> M

    style AI fill:#1a1a2e,stroke:#4a9eff,color:#ffffff
    style FUTURE fill:#1a2e1a,stroke:#4aff4a,color:#aaaaaa
```

---

## Development Workflow

1. Receive a task referencing an architecture document or ADR.
2. Read the relevant documents before writing any code.
3. Write tests first (TDD for frontend; alongside for backend).
4. Implement the smallest coherent unit.
5. Verify manually.
6. Commit with a conventional commit message.
7. Open a pull request and self-review against the checklist.
8. Update documentation if architecture or behaviour changed.
9. Stop. Wait for the next task.

Local development runs without cloud services. All external dependencies have local alternatives.

---

## Project Stages

| Stage | Name | Status | Description |
|---|---|---|---|
| 1 | Repository Foundation | ✅ Complete | Directory structure, root files, GitHub templates, CI workflow |
| 2 | Compose Foundation | ✅ Complete | Compose Multiplatform Android-first project with modular architecture |
| 3 | AI Workspace | ✅ Complete | Python AI workspace bootstrapped with uv, Pydantic schemas, base tests |
| 4 | Data Acquisition Framework | ✅ Complete | Extensible provider abstraction (football-data.co.uk, FBref, Understat) |
| 5 | Real Dataset Ingestion | ✅ Complete | Premier League 2023/24 dataset ingested and validated (380 matches) |
| 6 | Feature Engineering | ✅ Complete | 42 pre-match features: ELO, rolling form, H2H, rest days, league position |
| 7 | Model Training & Evaluation | ✅ Complete | XGBoost training pipeline, cross-validation, local model registry |
| 8 | Explainable AI | ✅ Complete | SHAP TreeExplainer pipeline, ExplanationService, global/local artifacts |
| 9 | Backend API | ✅ Complete | FastAPI service: /health, /model, /predict, /explain — 43 tests, OpenAPI docs |
| 10 | Football Intelligence Assistant | ✅ Complete | RAG assistant: Ollama, numpy vector store, POST /assistant/chat — 426 tests |
| 11 | Android Application | Planned | Compose Multiplatform screens consuming the backend API |
| 12 | Integration & Release | Planned | Structured evaluation, end-to-end testing, production readiness |

---

## AI Systems Overview

| System | Technology | Purpose |
|---|---|---|
| Prediction model | XGBoost | Match outcome prediction |
| Explainability | SHAP | Per-prediction feature importance |
| AI assistant | Ollama + RAG | Grounded football intelligence Q&A |
| Retrieval | Lightweight vector search | Ground assistant in processed data |
| Evaluation | Custom scripts in `ai/evaluation/` | Track quality metrics across runs |

The assistant never invents facts. Every response is grounded in retrieved data or model output. Fine-tuning and LoRA are out of scope.

---

## Frontend Module Graph

```
:app
 ├── :feature-home
 ├── :feature-prediction
 ├── :feature-match
 ├── :feature-team
 ├── :feature-assistant
 └── :feature-settings
       └── (all features depend on)
             ├── :core-ui
             ├── :core-design-system
             ├── :core-navigation
             ├── :core-model
             ├── :core-network
             └── :core-common

:core-testing  (test dependency only, never shipped)
```

Dependencies flow downward. Feature modules never depend on each other.

## Frontend Module Responsibilities

| Module | Layer | Purpose |
|---|---|---|
| `:app` | Presentation | Application entry point, DI assembly, root NavHost |
| `:feature-home` | Presentation | Recent matches and upcoming fixtures |
| `:feature-prediction` | Presentation | XGBoost prediction + SHAP explanation display |
| `:feature-match` | Presentation | Match detail and statistics |
| `:feature-team` | Presentation | Team profile and season stats |
| `:feature-assistant` | Presentation | RAG-powered football intelligence chat |
| `:feature-settings` | Presentation | User preferences and developer options |
| `:core-ui` | Presentation | Shared stateless Compose components |
| `:core-design-system` | Presentation | Material 3 tokens, theme, typography |
| `:core-navigation` | Presentation | Route definitions and navigation contracts |
| `:core-model` | Domain | Serializable domain types shared across layers |
| `:core-network` | Infrastructure | Ktor client configuration and base network layer |
| `:core-common` | Infrastructure | Shared utilities, coroutine helpers, base error types |
| `:core-testing` | Test | Test utilities, fakes, and base rules (never shipped) |

## AI Workspace

The `ai/` directory is a standalone Python project managed with [uv](https://github.com/astral-sh/uv).

```sh
cd ai

# Install all dependencies (including dev tools)
uv sync --extra dev

# Run linting
uv run ruff check .

# Check formatting
uv run black --check .

# Run type checking
uv run mypy .

# Run tests
uv run pytest
```

**Requires Python 3.12.** uv manages the virtual environment automatically; no manual `venv` activation is needed.

| Package | Purpose |
|---|---|
| `ingestion/` | Pull raw football data into `datasets/raw/` |
| `validation/` | Schema-validate data before it enters any pipeline |
| `preprocessing/` | Clean and normalise validated data into `datasets/processed/` |
| `feature_engineering/` | Compute model-ready features from preprocessed data |
| `schemas/` | Pydantic schema definitions — the data contract |
| `scripts/` | Operational CLI scripts (setup, pipeline triggers) |
| `tests/` | Unit tests mirroring the source structure |

---

## Build Instructions

Requires JDK 17 or higher.

```sh
cd frontend

# Build debug APK
./gradlew assembleDebug

# Run all unit tests
./gradlew testDebugUnitTest

# Static analysis
./gradlew detekt
./gradlew spotlessCheck

# Fix formatting
./gradlew spotlessApply
```

All commands resolve dependencies automatically on first run.

---

## Documentation Links

- [Project Instructions](.claude/CLAUDE.md)
- [Documentation Index](docs/README.md)
- [ADR Index](docs/adr/README.md)
- [AI Layer](ai/README.md)
- [Backend](backend/README.md)
- [Frontend](frontend/README.md)
- [Datasets](datasets/README.md)
- [Playbook](playbook/README.md)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines, commit conventions, and the code review checklist.

---

## License

MIT License. See [LICENSE](LICENSE).
