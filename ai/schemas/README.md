# schemas

Pydantic schema definitions for all football datasets.

## Responsibility

Defines the contract for every dataset the platform ingests and produces. Schemas are the single source of truth for field names, types, and constraints. Both validation and ingestion import from here.

## Contracts

- Every dataset has exactly one schema class derived from `pydantic.BaseModel`.
- Schemas use strict types. No `Any`. No optional fields without a documented reason.
- A schema change requires a new version. Old schemas are not deleted while data using them exists.

## Contents

- `match.py` — `RawMatch`, the provider-normalised football-data.co.uk row; `ProcessedMatch`, the canonical match row; and `MatchNormalizer`, which turns one into the other.
- `fixture.py` — `ProcessedFixture`, one upcoming match in the fixtures dataset (ADR 015).
