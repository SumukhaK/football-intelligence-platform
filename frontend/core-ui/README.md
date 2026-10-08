# :core-ui

Reusable Compose UI components shared across feature modules.

## Ownership

Presentation layer — shared components only. Feature-specific UI lives in feature modules. Depends on `core-model` and `core-design-system`.

## Contents

- `KickoffLoader` — the app's loading animation: home, draw and away arcs filling in around a ball, matching the launch screen (ADR 016). Used for every loading state.
- `LoadingView`, `ErrorView`, `errorMessage` — full-screen loading (with `KickoffLoader`) and plain-language error states.
- `OfflineBanner`, `RefreshableContent` — the offline notice and pull to refresh.
- `StatusChip`, `BackButton` — small shared controls.
- `TeamCrest`, `LeagueEmblem` — a team's crest or a league's emblem loaded with Coil, with a plain shield while loading or when there is none. The image URLs come from `LocalCrestUrl` and `LocalEmblemUrl`, which the app provides (ADR 020).
- `PreviewSurface` — wrapper for `@Preview` functions.

## Constraints

- Components must be stateless. They receive state and emit events.
- Every component has a `@Preview`.
- No business logic. No ViewModels.
- No feature-specific code.
