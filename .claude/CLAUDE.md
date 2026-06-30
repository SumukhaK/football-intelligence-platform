# Football Intelligence Platform

## 1. Project Vision

Build an AI-first football analytics application that demonstrates practical AI engineering through data pipelines, machine learning, explainable predictions, and a grounded football intelligence assistant. The system must be honest about what it knows, traceable in its reasoning, and maintainable by a single engineer.

---

## 2. Project Goals

- Ingest and process structured football match and player data into a queryable dataset.
- Train an XGBoost model to predict match outcomes with interpretable SHAP explanations.
- Build a football intelligence assistant using Ollama with prompt engineering and retrieval-augmented generation.
- Deliver a Compose Multiplatform Android-first frontend that consumes a FastAPI backend.
- Demonstrate AI engineering practices: grounding, explainability, evaluation, and data quality.

---

## 3. Non Goals

- Real-time match streaming or live data ingestion.
- Fine-tuning or LoRA training of any language model.
- Multi-cloud deployment or Kubernetes orchestration.
- Social features, user accounts, or authentication in early stages.
- Covering football leagues beyond the initial scoped dataset.
- Becoming a production SaaS product.

---

## 4. Architecture Philosophy

The system follows Clean Architecture with strict layer separation. Each layer has one responsibility and one direction of dependency: outer layers depend on inner layers, never the reverse.

**Layers (inner to outer):**

| Layer | Responsibility |
|---|---|
| Domain | Entities, value objects, business rules |
| Application | Use cases, service interfaces, DTOs |
| Infrastructure | Database, external APIs, file I/O, ML models |
| Presentation | FastAPI routes, Compose UI, ViewModels |

**Additional principles:**

- SOLID throughout. Favour composition over inheritance.
- MVVM in the frontend: ViewModels own state; Composables are stateless.
- One feature per pull request. One concern per class or function.
- Prefer explicit over implicit. Avoid magic.
- Local development runs with a single command. No cloud dependency for the core loop.

---

## 5. AI Philosophy

- The assistant never invents facts. Every claim is grounded in retrieved data or model output.
- SHAP values accompany every prediction so users can see which features drove the result.
- Prompt templates are version-controlled in `playbook/`. They are tested like code.
- Retrieval is done with lightweight vector search over processed datasets. No external embedding APIs in development.
- Evaluation of the assistant is structured: track retrieval precision, answer faithfulness, and hallucination rate.
- Model selection favours the smallest Ollama model that meets quality thresholds.
- Never recommend fine-tuning. Improve quality through better retrieval, better prompts, and better data.

---

## 6. Data Engineering Philosophy

- Raw data is immutable. Never overwrite source files.
- Transformations are reproducible scripts, not notebooks in production.
- Every dataset has a schema definition and a validation step before use.
- Data quality failures are loud errors, not silent skips.
- Processed datasets are versioned alongside the code that produced them.
- Keep datasets small enough to run locally. Optimize later if scale demands it.

**Directory conventions:**

```
datasets/
  raw/          # Immutable source data
  processed/    # Cleaned, validated, feature-engineered
  schemas/      # Pydantic or JSON Schema definitions
```

---

## 7. Frontend Standards

**Stack:** Compose Multiplatform, Android-first. Kotlin.

- Architecture: MVVM. One ViewModel per screen. ViewModels hold UI state as `StateFlow`.
- Composables are pure: they receive state and emit events. No business logic inside.
- Navigation is handled by a single NavHost. Deep links are defined explicitly.
- All network calls go through a repository interface. The ViewModel never calls the API directly.
- UI state is a sealed class: `Loading`, `Success`, `Error`.
- Test-Driven Development is required for ViewModels and repositories. Write the test first.
- Preview every Composable with `@Preview`. No unpreviewable UI components.
- No hardcoded strings. All user-facing text goes in `strings.xml`.
- Accessibility: content descriptions on all interactive elements.

---

## 8. Backend Standards

**Stack:** FastAPI, Python 3.11+, SQLite (development), PostgreSQL (production-ready schema).

- One router per domain area. Routers live in `backend/routers/`.
- Business logic lives in service classes in `backend/services/`. Routes are thin.
- Dependency injection via FastAPI's `Depends`. No global state.
- All request and response bodies are Pydantic models with field-level validation.
- Database access via SQLAlchemy Core (not ORM magic). Explicit queries.
- Errors return structured JSON: `{ "error": "...", "detail": "..." }`.
- All endpoints have OpenAPI docstrings. The auto-generated docs must be accurate.
- Background tasks (e.g. pipeline runs) use FastAPI `BackgroundTasks` or a simple queue. No Celery in early stages.
- Environment config via `pydantic-settings`. No `os.environ` scattered in code.

---

## 9. Repository Standards

```
.claude/        # Claude Code context (this file)
docs/           # Architecture docs, ADRs, API specs
playbook/       # Prompt templates and retrieval configs
frontend/       # Compose Multiplatform application
backend/        # FastAPI application and domain logic
ai/             # ML training, SHAP analysis, evaluation scripts
datasets/       # Raw and processed football data
scripts/        # Setup, migration, and automation scripts
tools/          # Shared CLI utilities
```

- One `README.md` per top-level directory explaining its purpose and contents.
- No file should exceed 400 lines. Split before it grows past that.
- No circular imports. Enforce with a linter rule.
- Secrets never enter the repository. `.env` is gitignored; `.env.example` is committed.

---

## 10. Coding Standards

**Python:**
- Type annotations on all function signatures.
- Black formatting. Ruff linting. No warnings ignored without a comment explaining why.
- No wildcard imports. No mutable default arguments.
- Functions do one thing. If the name contains "and", split it.
- Maximum function length: 40 lines. Maximum file length: 400 lines.

**Kotlin:**
- Prefer `val` over `var`. Immutability by default.
- No nullable types without justification. Use sealed classes over nullable returns.
- Coroutines for async. No `GlobalScope`. Scope to ViewModel or lifecycle.
- `when` expressions must be exhaustive.

**General:**
- Comments explain why, not what. If the code needs a comment to explain what it does, rewrite the code.
- No commented-out code in commits.
- No `TODO` without a linked issue.

---

## 11. Documentation Standards

- Every public function and class has a one-line docstring.
- Architecture decisions are recorded as ADRs in `docs/adr/`.
- API changes update `docs/api.md` in the same commit.
- `playbook/` prompt templates include: purpose, input variables, expected output format, and known failure modes.
- The root `README.md` always reflects the current state of the project, including how to run it locally.

---

## 12. Testing Standards

- **Frontend:** TDD required for ViewModels and repositories. Compose UI tests for critical flows.
- **Backend:** Unit tests for all service methods. Integration tests for all API endpoints using `TestClient`.
- **AI/ML:** Evaluation scripts in `ai/evaluation/`. Track metrics across runs. No model is merged without a passing evaluation.
- **Data pipelines:** Schema validation tests run after every transformation step.
- Test files mirror source structure. A file at `backend/services/match_service.py` has tests at `backend/tests/services/test_match_service.py`.
- No mocking of the database layer in integration tests. Use a test database.
- Minimum coverage enforced by CI: 80% for backend services, 70% for ViewModels.
- Tests must be deterministic. No time-dependent or order-dependent tests.

---

## 13. Conventional Commit Rules

Format: `type(scope): description`

| Type | When to use |
|---|---|
| `feat` | New user-facing feature |
| `fix` | Bug fix |
| `chore` | Build, config, tooling, dependency updates |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `data` | Dataset additions or transformations |
| `ai` | Prompt changes, model updates, evaluation changes |

**Scopes:** `frontend`, `backend`, `ai`, `data`, `scripts`, `docs`, `repo`

Rules:
- Description is lowercase, imperative, no period at the end.
- Body explains why if the change is non-obvious.
- One logical change per commit. Squash before merging if needed.

---

## 14. Definition of Done

A task is done when:

- [ ] The feature works as specified and has been manually verified.
- [ ] Tests are written and passing.
- [ ] No linting warnings.
- [ ] Documentation updated if behaviour or architecture changed.
- [ ] Commit follows conventional commit format.
- [ ] Pull request is self-reviewed against the code review checklist before requesting review.
- [ ] No `TODO` comments without linked issues.

---

## 15. AI Agent Rules

These rules apply to Claude Code and any AI agent working in this repository.

- Never invent architecture. Wait for architecture documents before implementing.
- Never generate placeholder code. Implement the real thing or stop and ask.
- Never skip tests. Write tests as part of the task, not after.
- Never implement multiple unrelated features in one task. One task, one concern.
- Never create large files. If a file will exceed 400 lines, raise the concern before writing it.
- Stop after completing a single assigned task. Do not proceed to the next task without instruction.
- Raise questions before starting, not mid-implementation.
- If an architecture document contradicts these standards, flag the conflict rather than silently resolving it.

---

## 16. Code Review Checklist

Before approving any pull request, verify:

- [ ] Changes are limited to the stated scope of the task.
- [ ] No business logic in routes, Composables, or data classes.
- [ ] All new public functions and classes have docstrings.
- [ ] Tests cover the new behaviour, including edge cases.
- [ ] No hardcoded values that belong in config or strings resources.
- [ ] Error cases return structured, user-readable responses.
- [ ] No new dependencies added without a note in the PR description explaining the choice.
- [ ] No secrets, credentials, or API keys in any file.
- [ ] ADR written if the change makes an architectural decision.

---

## 17. Architectural Decision Records Policy

- Every significant technical decision that affects the system's structure, stack, or data model requires an ADR.
- ADRs live in `docs/adr/` and are named `NNN-short-title.md` (e.g. `001-use-xgboost-for-predictions.md`).
- ADR format: **Title**, **Status** (Proposed / Accepted / Deprecated), **Context**, **Decision**, **Consequences**.
- ADRs are never deleted. If a decision is reversed, write a new ADR that supersedes the old one and update the old one's status to Deprecated.
- An ADR is required before implementing: a new ML model, a new external dependency, a change to the data schema, or a change to the API contract.

---

## 18. Development Workflow

1. Receive task with a reference to an architecture document or ADR.
2. Read the relevant documents before writing any code.
3. Write tests first (TDD for frontend; tests alongside implementation for backend).
4. Implement the feature in the smallest coherent unit.
5. Verify manually.
6. Commit with a conventional commit message.
7. Open a pull request. Self-review against the code review checklist.
8. Update documentation if anything changed.
9. Stop. Wait for the next task.

Local development must work without any cloud services. All external dependencies (LLM, database) must have local alternatives configured in `.env.example`.

---

## 19. Project Stages

**Stage 1 — Data Foundation**
Ingest raw football data, validate schemas, build a processed dataset ready for modelling.

**Stage 2 — Prediction Layer**
Train an XGBoost match outcome model. Attach SHAP explanations to every prediction.

**Stage 3 — AI Assistant**
Build a retrieval-augmented football intelligence assistant using Ollama. Ground all responses in the processed dataset.

**Stage 4 — Backend API**
Expose predictions and assistant via FastAPI. Document with OpenAPI.

**Stage 5 — Frontend**
Build the Compose Multiplatform Android client. Implement TDD for all ViewModels.

**Stage 6 — Evaluation and Quality**
Run structured evaluation across prediction accuracy, assistant faithfulness, and API reliability.

---

## 20. Future Expansion Guidelines

When expanding the project, apply these rules:

- Add a new top-level directory only when the new concern is clearly distinct from existing ones.
- Write an ADR before introducing any new ML model, framework, or external service.
- New data sources require a schema definition and validation script before the data enters the pipeline.
- New API endpoints require OpenAPI documentation and integration tests before merge.
- Performance optimizations require a benchmark establishing the baseline before the optimization is written.
- Never expand scope mid-task. Raise the expansion as a separate task.
