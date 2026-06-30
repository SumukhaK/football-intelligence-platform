# schemas

Pydantic schema definitions for all football datasets.

## Responsibility

Defines the contract for every dataset the platform ingests and produces. Schemas are the single source of truth for field names, types, and constraints. Both validation and ingestion import from here.

## Contracts

- Every dataset has exactly one schema class derived from `pydantic.BaseModel`.
- Schemas use strict types. No `Any`. No optional fields without a documented reason.
- A schema change requires a new version. Old schemas are not deleted while data using them exists.
- JSON Schema exports live alongside the Pydantic models and are regenerated on change.

## Future Contents

- `match.py` — `RawMatch`, `ProcessedMatch` schema definitions.
- `team.py` — `Team` schema definition.
- `player.py` — `Player` schema definition.
- `features.py` — `MatchFeatureRow` schema definition (input contract for the model).
