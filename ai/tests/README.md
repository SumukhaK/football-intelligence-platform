# tests

Unit and integration tests for the AI data engineering workspace.

## Responsibility

Verifies ingestion, validation, feature engineering, training, explainability, the goals model, the assistant and the FastAPI backend. Tests mirror the source structure.

## Structure

```
tests/
  test_bootstrap.py          # Verifies packages import and dependencies are installed
  test_config.py, test_leagues.py, test_storage.py
  ingestion/                 # Tests for ai/ingestion/ (backfill, live refresh, fixtures)
  providers/                 # Tests for ai/providers/
  validation/                # Tests for ai/validation/
  schemas/                   # Tests for ai/schemas/
  metadata/                  # Tests for ai/metadata/
  feature_engineering/       # Tests for ai/feature_engineering/
  training/                  # Tests for ai/training/
  evaluation/                # Tests for ai/evaluation/
  model_registry/            # Tests for ai/model_registry/
  inference/                 # Tests for ai/inference/
  explainability/            # Tests for ai/explainability/
  goals/                     # Tests for ai/goals/
  assistant/                 # Tests for ai/assistant/
  backend/                   # Endpoint, versioning, rate limit and service tests for ai/backend/
  integration/               # End-to-end tests against the real model (marked integration)
```

Run everything with `uv run pytest`, or skip the integration tests with
`uv run pytest -m "not integration"`.

## Contracts

- Test files mirror source structure: `ingestion/backfill.py` → `tests/ingestion/test_backfill.py`.
- No test touches external filesystems or network unless marked `@pytest.mark.integration`.
- Tests are deterministic. No time-dependent or order-dependent behaviour.
- Minimum coverage: 70% for the whole workspace (`fail_under` in `ai/pyproject.toml`, enforced in CI).
- Data quality failures must be tested explicitly — every validation rule has a failing case.
