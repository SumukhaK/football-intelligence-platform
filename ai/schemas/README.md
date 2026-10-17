# schemas

Pydantic schema definitions for all football datasets.

## Responsibility

Defines canonical match and fixture row contracts. Both validation and ingestion import from here. Provider metadata, feature artifacts and model/evaluation outputs also have their own models in their owning packages.

## Contracts

- Canonical rows are validated with Pydantic models and field constraints; default Pydantic coercion still applies where strict validation is not requested.
- Optional fields represent source data that may be absent; callers must respect those contracts.
- A schema change requires a new version. Old schemas are not deleted while data using them exists.

## Contents

- `match.py` — `RawMatch`, the provider-normalised football-data.co.uk row; `ProcessedMatch`, the canonical match row; and `MatchNormalizer`, which turns one into the other.
- `fixture.py` — `ProcessedFixture`, one upcoming match in the fixtures dataset (ADR 015).
