# Datasets

Football match, player, and competition data at various stages of processing.

---

## Ownership

Managed by the AI layer. Raw data is immutable. All transformations are reproducible scripts in `ai/`.

---

## Directory Structure

```
datasets/
  raw/        # Immutable source data. Never modified after ingestion.
  interim/    # Intermediate outputs between transformation steps.
  processed/  # Validated, feature-engineered data ready for modelling and retrieval.
  external/   # Third-party reference data (league tables, player registries).
```

---

## Rules

- Raw data is never overwritten or modified. If a source file needs correction, document the issue and re-ingest.
- Every dataset has a schema definition in `ai/validation/`. Validation runs before any downstream step.
- Data quality failures are loud errors. Silent skips are not acceptable.
- Processed datasets are versioned alongside the scripts that produced them.
- Datasets are kept small enough to run locally. Large datasets are documented but not committed.

---

## What is Committed

- `raw/` — gitignored by default. Ingestion scripts recreate it.
- `interim/` — gitignored. Reproducible from raw data.
- `processed/` — gitignored by default. Committed only when explicitly versioned for a release.
- `external/` — gitignored. Sourced from documented external locations.
- Schema definitions in `ai/validation/` — always committed.

---

## Future Responsibilities

- Multi-league datasets.
- Player-level event data.
- Historical odds data for model calibration.
