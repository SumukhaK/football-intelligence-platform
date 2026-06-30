# validation

Schema and data quality validation for the football AI pipeline.

## Responsibility

All data entering the pipeline must pass validation before moving to the next
stage. This package provides two complementary validators:

- `DatasetValidator` — rule-based quality checks (nulls, duplicates, row counts).
- `SchemaValidator` — Pydantic-schema-based column compatibility checks.

Validation failures are explicit errors, not silent skips.

## DatasetValidator

Applies an ordered list of `ValidationRule` objects to a DataFrame. All rules
are run regardless of failures so the caller sees the complete error picture.

```python
from validation.dataset_validator import (
    DatasetValidator, RequiredColumnsRule, NullConstraintRule, DuplicateRowRule,
)

validator = DatasetValidator()
result = validator.validate(df, [
    RequiredColumnsRule(["date", "home_team", "away_team", "home_goals_ft"]),
    NullConstraintRule(["date", "home_team", "away_team"]),
    DuplicateRowRule(max_ratio=0.01),
])
if not result.passed:
    raise ValidationError("match_results", str(result.errors))
```

## Available Rules

| Rule | Failure Condition |
|---|---|
| `RequiredColumnsRule(required)` | Any listed column is absent |
| `NullConstraintRule(non_nullable)` | Any listed column contains nulls |
| `DuplicateRowRule(max_ratio)` | Duplicate fraction exceeds `max_ratio` |
| `RowCountRule(min_rows)` | DataFrame has fewer than `min_rows` rows |

## SchemaValidator

Validates that a DataFrame's columns are compatible with a Pydantic model.
Required fields must be present. Optional fields may be absent. Unknown
columns produce warnings in `validate()` and errors in `validate_strict()`.

## Contracts

- Every dataset entering preprocessing must pass `DatasetValidator`.
- A failed `ValidationResult` must never be silently ignored.
- Every validation rule has at least one test covering both the passing
  and failing case.
