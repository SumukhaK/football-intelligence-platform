# :core-model

Domain model classes shared across feature modules and the network layer.

## Ownership

Domain layer. These types flow from the network layer through to the UI. No module depends on `core-model` except to read these types.

## Future Contents

- `Match` — match result and metadata.
- `Team` — team identity and statistics.
- `Player` — player profile and season stats.
- `Prediction` — XGBoost match outcome prediction with SHAP features.
- `AssistantMessage` — AI assistant conversation turn.

## Constraints

- Pure Kotlin only in `commonMain`. No Android framework.
- No business logic. These are data structures, not services.
- All types are serializable with `@Serializable`.
