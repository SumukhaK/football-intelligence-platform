# ingestion

Pulls raw football data from source files into `datasets/raw/`.

## Responsibility

This package owns the boundary between external data sources and the platform. It reads source files, applies no transformations, and writes immutable raw snapshots to `datasets/raw/`.

## Contracts

- Raw data is never modified after ingestion. Treat `datasets/raw/` as append-only.
- Every ingestion run must record: source identifier, timestamp, row count, and file hash.
- Data quality failures are loud errors, not silent skips.

## Future Contents

- `loaders/` — source-specific loader classes (CSV, JSON, API).
- `runner.py` — CLI entry point for running an ingestion pipeline.
