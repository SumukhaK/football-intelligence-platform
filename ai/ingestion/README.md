# ingestion

Pulls raw football data from source files into `datasets/raw/`.

## Responsibility

This package owns the boundary between external data sources and the platform. It preserves source bytes as immutable raw snapshots, then normalises and validates canonical match/fixture outputs under `datasets/processed/`.

## Contracts

- Raw data is never modified after ingestion. Treat `datasets/raw/` as append-only.
- Every ingestion run must record: source identifier, timestamp, row count, and file hash.
- Normalisation failures are counted and reported. Multi-season ingestion fails above its allowed malformed-row threshold (0.5%) or on integrity failures; the legacy single-season pipeline can report skipped rows.

## Contents

- `downloader.py`, `pipeline.py` — download one provider dataset, validate it and store raw and canonical copies.
- `backfill.py` — every season of the five leagues from football-data.co.uk (ADR 005).
- `in_progress.py`, `live_refresh.py` — the season so far, appended to history as the served live dataset (ADR 008, ADR 013).
- `fixtures.py` — upcoming fixtures from openfootball, renamed to football-data team names and validated (ADR 015).
- `storage.py` — immutable raw partitions and versioned processed files.
