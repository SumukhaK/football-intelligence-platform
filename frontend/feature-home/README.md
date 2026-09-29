# :feature-home

The app's first screen: upcoming fixtures by date, one tab per league.

## Ownership

Presentation layer. Depends on `core-ui`, `core-design-system`, `core-model`, `core-navigation`.

## Contents

- `HomeViewModel` — upcoming fixtures for the selected league tab, grouped by day in the phone's time zone.
- `HomeScreen` — league tabs (Premier League first) over the fixtures list, with pull to refresh and the offline banner.
- `FixturesRepository` — reads `GET /v2/fixtures`.
- `BackendStatusViewModel`, `BackendStatusSection` — the backend status card shown on the Settings screen.
- `HealthRepository` — reads `GET /v2/health`.

## Constraints

- ViewModel written test-first. No ViewModel without a passing test.
- No direct API calls from the ViewModel. All data goes through the repository.
- No hardcoded strings.
