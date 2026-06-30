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

| Stage | Name | Description |
|---|---|---|
| 1 | Data Foundation | Ingest raw football data, validate schemas, build processed dataset |
| 2 | Prediction Layer | Train XGBoost model, attach SHAP explanations to every prediction |
| 3 | AI Assistant | Build RAG assistant using Ollama, ground all responses in data |
| 4 | Backend API | Expose predictions and assistant via FastAPI with OpenAPI docs |
| 5 | Frontend | Build Compose Multiplatform Android client with TDD ViewModels |
| 6 | Evaluation | Structured evaluation of prediction accuracy and assistant quality |

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
