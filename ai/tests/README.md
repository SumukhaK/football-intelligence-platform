# tests

Unit and integration tests for the AI data engineering workspace.

## Responsibility

Verifies the correctness of ingestion logic, validation rules, preprocessing transformations, and feature engineering functions. Tests mirror the source structure.

## Structure

```
tests/
  test_bootstrap.py          # Verifies packages import and dependencies are installed
  ingestion/                 # Tests for ai/ingestion/
  validation/                # Tests for ai/validation/
  preprocessing/             # Tests for ai/preprocessing/
  feature_engineering/       # Tests for ai/feature_engineering/
  schemas/                   # Tests for ai/schemas/
```

## Contracts

- Test files mirror source structure: `ingestion/loader.py` → `tests/ingestion/test_loader.py`.
- No test touches external filesystems or network unless marked `@pytest.mark.integration`.
- Tests are deterministic. No time-dependent or order-dependent behaviour.
- Minimum coverage: 70% per package (enforced in CI).
- Data quality failures must be tested explicitly — every validation rule has a failing case.
