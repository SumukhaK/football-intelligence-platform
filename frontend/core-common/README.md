# :core-common

Shared utilities, extension functions, and base types used across all modules.

## Ownership

Infrastructure. No feature or presentation logic.

## Contents

- `DispatcherProvider` — injectable coroutine dispatchers, so tests can swap them.
- `formatSavedAt` — when offline data was saved, e.g. "29 Sep, 14:30" (`androidMain`).
- `fixtureDay`, `formatKickoff`, `formatMatchDay` — fixture dates and kick-off times in the phone's time zone (`androidMain`).

## Constraints

- No Compose dependencies.
- No Android framework dependencies in `commonMain`.
- No business logic.
