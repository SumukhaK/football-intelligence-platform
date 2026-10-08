# Datasets

Football match, player, and competition data at various stages of processing.

---

## Ownership

Managed by the AI layer. Raw data is immutable. All transformations are reproducible scripts in `ai/`.

---

## Directory Structure

```
datasets/
  raw/        # Immutable source data, one folder per provider:
              #   football_data/ results · openfootball/ fixtures · kaggle/ experiment inputs
  processed/  # Validated datasets: football_data/ matches (top 5, live) · openfootball/ fixtures
  features/   # Feature matrices and their metadata (metadata is committed)
  schemas/    # Reference data: team_aliases.csv canonical team names, team_crests.csv and league_emblems.csv image URLs (committed)
  interim/    # Intermediate outputs between transformation steps
  external/   # Third-party reference data
```

---

## Rules

- Raw data is never overwritten or modified. If a source file needs correction, document the issue and re-ingest.
- Every dataset has a schema definition in `ai/schemas/` and validation in `ai/validation/`. Validation runs before any downstream step.
- Data quality failures are loud errors. Silent skips are not acceptable.
- Processed datasets are versioned alongside the scripts that produced them.
- Datasets are kept small enough to run locally. Large datasets are documented but not committed.

---

## What is Committed

- `raw/` — gitignored by default. Ingestion scripts recreate it.
- `interim/` — gitignored. Reproducible from raw data.
- `processed/` — gitignored by default. Committed only when explicitly versioned for a release.
- `external/` — gitignored. Sourced from documented external locations.
- `schemas/team_aliases.csv`, `schemas/team_crests.csv`, `schemas/league_emblems.csv` and feature metadata under `features/` — always committed.
- Schema definitions in `ai/schemas/` — always committed.
