# validation

Validates ingested data against Pydantic schema definitions before it enters any pipeline.

## Responsibility

Every dataset entering the pipeline passes through validation. If the data does not conform to the schema, the pipeline stops with a structured error. Silent data degradation is not permitted.

## Contracts

- All schemas are defined in `schemas/`. Validation reads from there; it does not define its own.
- Validation produces a `ValidationReport`: pass/fail, row count, field-level error summary.
- A dataset that fails validation must never reach preprocessing.

## Future Contents

- `validator.py` — `DatasetValidator` class that wraps a Pydantic model and a DataFrame.
- `report.py` — `ValidationReport` dataclass.
