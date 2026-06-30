# Contributing

This document describes how to contribute to the Football Intelligence Platform.

---

## Before You Start

Read [.claude/CLAUDE.md](.claude/CLAUDE.md) in full. It defines the architecture, coding standards, testing requirements, and commit conventions that all contributions must follow.

---

## Development Workflow

1. Pick a task that references an architecture document or ADR.
2. Read the relevant documents before writing any code.
3. Write tests first for frontend ViewModels and repositories (TDD).
4. Implement the smallest coherent unit that satisfies the task.
5. Verify the change manually.
6. Commit using the conventional commit format below.
7. Open a pull request and complete the self-review checklist.
8. Update documentation if behaviour or architecture changed.

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
- One logical change per commit.

---

## Pull Request Guidelines

- One feature or fix per pull request.
- Title follows the conventional commit format.
- Description explains what changed and why.
- All items on the self-review checklist must be checked before requesting review.

### Self-Review Checklist

- [ ] Changes are limited to the stated scope of the task.
- [ ] No business logic in routes, Composables, or data classes.
- [ ] All new public functions and classes have docstrings.
- [ ] Tests cover the new behaviour, including edge cases.
- [ ] No hardcoded values that belong in config or string resources.
- [ ] Error cases return structured, user-readable responses.
- [ ] No new dependencies added without a note in the PR description.
- [ ] No secrets, credentials, or API keys in any file.
- [ ] ADR written if the change makes an architectural decision.

---

## Architectural Decision Records

Any change that affects system structure, stack choice, or data model requires an ADR in `docs/adr/` before implementation begins. See [docs/adr/README.md](docs/adr/README.md).

---

## Code Style

- **Python:** Black formatting, Ruff linting, type annotations on all signatures.
- **Kotlin:** Prefer `val`, sealed classes over nullables, exhaustive `when` expressions.
- No commented-out code. No `TODO` without a linked issue. Comments explain why, not what.

---

## Testing Requirements

- Frontend: TDD for all ViewModels and repositories.
- Backend: Unit tests for service methods, integration tests for all API endpoints.
- AI: Evaluation scripts must pass before any model change is merged.
- Data: Schema validation after every transformation step.
