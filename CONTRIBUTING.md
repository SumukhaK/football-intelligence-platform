# Contributing

This document describes how to contribute to the Football Intelligence Platform.

---

## Before You Start

Read [.claude/CLAUDE.md](.claude/CLAUDE.md) in full. It defines the architecture, coding standards, testing requirements, and commit conventions that all contributions must follow.

Read the relevant architecture documents and ADRs in `docs/adr/` before writing any code.

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-ready code. Tagged releases only. |
| `develop` | Integration branch. All feature branches merge here. |
| `feature/<scope>-<description>` | One feature or fix per branch. |
| `release/v<major>.<minor>.<patch>` | Release preparation. Created from `develop`. |
| `hotfix/<description>` | Critical fixes that cannot wait for a release cycle. Branches from `main`, merges to both `main` and `develop`. |

Branch names use kebab-case. Scope prefixes match the conventional commit scopes: `ai`, `frontend`, `backend`, `docs`, `data`, `scripts`, `repo`.

**Examples:**
```
feature/ai-stage8-shap-explainability
feature/backend-prediction-router
feature/docs-api-reference
hotfix/ai-training-nan-imputation
```

---

## Development Workflow

1. Create a branch from `develop`.
2. Read the relevant architecture document or ADR before writing any code.
3. Write tests first (TDD for frontend ViewModels and repositories; alongside implementation for backend and AI).
4. Implement the smallest coherent unit that satisfies the task.
5. Run all quality checks and confirm they pass.
6. Verify the change manually.
7. Commit using the conventional commit format below.
8. Open a pull request targeting `develop`.
9. Complete the self-review checklist before requesting review.
10. Update documentation if behaviour or architecture changed.

---

## Quality Checks

### AI workspace (`ai/`)

```sh
cd ai
uv sync --extra dev

uv run ruff check .         # must print: All checks passed!
uv run black --check .      # must print: N files would be left unchanged.
uv run mypy .               # must print: Success: no issues found
uv run pytest               # must print: N passed (no failures)
```

All four checks must pass before opening a pull request.

### Android workspace (`frontend/`)

```sh
cd frontend
./gradlew spotlessCheck     # formatting
./gradlew detekt            # static analysis
./gradlew testDebugUnitTest # unit tests
```

---

## Conventional Commits

Format: `type(scope): description`

| Type | When to use |
|---|---|
| `feat` | New user-facing feature |
| `fix` | Bug fix |
| `chore` | Build, config, tooling, dependency updates |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `refactor` | Code change that is neither a bug fix nor a feature |
| `data` | Dataset additions or transformations |
| `ai` | Prompt changes, model updates, evaluation changes |

**Scopes:** `frontend`, `backend`, `ai`, `data`, `scripts`, `docs`, `repo`

Rules:
- Description is lowercase, imperative, no period at the end.
- Body explains why if the change is non-obvious.
- One logical change per commit. Squash before merging if needed.

**Examples:**
```
feat(ai): add rolling form feature generator
fix(ai): correct shift(1) application in elo rating feature
docs(repo): add cli reference guide
chore(frontend): update compose bom to 2024.09.00
test(ai): add edge cases for head-to-head with no prior history
refactor(ai): extract team match view builder to shared helper
data(data): ingest premier league 2023/24 season
ai(ai): update training config to use early stopping patience of 10
```

---

## Pull Request Guidelines

- One feature or fix per pull request.
- Title follows the conventional commit format.
- Description explains what changed and why.
- All items on the self-review checklist must be checked before requesting review.
- Pull requests must target `develop`, not `main`.
- Do not squash commits unless specifically requested in review.

### Self-Review Checklist

Before requesting review, confirm every item:

- [ ] Changes are limited to the stated scope of the task.
- [ ] No business logic in routes, Composables, or data classes.
- [ ] All new public functions and classes have one-line docstrings.
- [ ] Tests cover the new behaviour, including edge cases.
- [ ] No hardcoded values that belong in config or string resources.
- [ ] Error cases return structured, user-readable responses.
- [ ] No new dependencies added without a note in the PR description explaining the choice.
- [ ] No secrets, credentials, or API keys in any file.
- [ ] ADR written if the change makes an architectural decision.
- [ ] All quality checks pass (ruff, black, mypy, pytest or Gradle equivalent).
- [ ] Documentation updated if behaviour or architecture changed.

---

## Coding Standards

### Python

- Type annotations on all function signatures. No exceptions.
- Black formatting (line length 88). Ruff linting. No warnings ignored without an explanatory comment.
- No wildcard imports. No mutable default arguments.
- Functions do one thing. If the name contains "and", split it.
- Maximum function length: 40 lines. Maximum file length: 400 lines.
- Comments explain why, not what. If the code needs a comment to explain what it does, rewrite the code.
- No commented-out code in commits.
- No `TODO` without a linked issue.

### Kotlin

- Prefer `val` over `var`. Immutability by default.
- No nullable types without justification. Use sealed classes over nullable returns.
- Coroutines for async. No `GlobalScope`. Scope to ViewModel or lifecycle.
- `when` expressions must be exhaustive.

---

## Testing Requirements

- **Frontend:** TDD required for all ViewModels and repositories. Compose UI tests for critical user flows.
- **Backend:** Unit tests for all service methods. Integration tests for all API endpoints using `TestClient`. No mocking of the database layer in integration tests.
- **AI:** Unit tests alongside every new module. Evaluation scripts must pass before any model change is merged.
- **Data:** Schema validation tests run after every transformation step.

Test files mirror source structure:
- `ai/tests/training/test_trainer.py` tests `ai/training/trainer.py`
- `backend/tests/services/test_match_service.py` tests `backend/services/match_service.py`

Minimum coverage enforced by CI:
- Backend services: 80%
- Frontend ViewModels: 70%

Tests must be deterministic. No time-dependent or order-dependent tests.

---

## Architectural Decision Records

Any change that affects system structure, stack choice, or data model requires an ADR in `docs/adr/` before implementation begins.

An ADR is required before:
- Introducing a new ML model or algorithm.
- Adding a new external dependency or service.
- Changing the data schema.
- Changing the API contract.
- Making a structural change to any architecture layer.

See [docs/adr/README.md](docs/adr/README.md) for the ADR format and index.

---

## Documentation Expectations

- Every public function and class has a one-line docstring.
- Architecture changes update or add an ADR.
- API changes update `docs/api.md` in the same commit.
- New CLI commands are added to `docs/reference/cli.md`.
- Stage completion produces a `docs/reports/stage-NN-summary.md`.

---

## Merge Policy

- Pull requests require at least one approval before merging.
- All CI checks must pass.
- No direct commits to `develop` or `main`.
- Merge commits are preferred over squash or rebase, to preserve feature branch history.
- `main` receives only tagged release commits merged from `release/*` branches.
