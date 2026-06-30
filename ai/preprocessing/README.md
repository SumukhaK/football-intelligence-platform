# preprocessing

Cleans and normalises validated raw data into `datasets/processed/`.

## Responsibility

Transforms validated raw records into a clean, consistent form ready for feature engineering. This layer handles missing value strategy, type coercion, deduplication, and outlier policy.

## Contracts

- Preprocessing only reads from `datasets/raw/`. It never reads unvalidated files.
- Every transformation is a deterministic, testable function with no side effects.
- Processed data is written to `datasets/processed/` with a version suffix matching the pipeline run.
- Raw source files are never modified.

## Future Contents

- `cleaners/` — per-dataset cleaning functions.
- `normaliser.py` — shared normalisation utilities (date parsing, string standardisation).
- `runner.py` — CLI entry point for a preprocessing run.
