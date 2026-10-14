# :core-model

Domain model classes shared across feature modules and the network layer.

## Ownership

Domain layer. These types flow from the network layer through to the UI. No module depends on `core-model` except to read these types.

## Contents

- `HealthStatus`, `ModelInfo` — server and model status.
- `CompetitionsResponse`, `TeamsResponse` — served leagues and their teams.
- `FixturesResponse`, `Fixture`, `SERVED_LEAGUES` — upcoming fixtures and the league tab order.
- `PredictionRequest`, `PredictionResult` — win/draw/loss prediction with the draw tag.
- `ExplanationResult`, `FeatureContribution` — SHAP attribution with fan-friendly labels.
- `Insights` — likely scores and goal markets from the goals model.
- `ChatRequest`, `ChatResponse` — assistant conversation.
- `LoginRequest`, `RedeemInviteRequest`, `SessionResponse`, `Me`, `ConsentRequest`, `TokenStore` — sign-in and consent (ADR 022).
- `FavouriteTeam`, `FavouriteTeamStore` — the favourite team saved on the device.
- `TeamOutlook` — a team's projected season finish (ADR 023).
- `NetworkResult`, `ErrorKind` — typed result of every API call; `Success.cachedAt` marks saved data replayed offline.

## Constraints

- Pure Kotlin only in `commonMain`. No Android framework.
- No business logic. These are data structures, not services.
- All types are serializable with `@Serializable`.
