# :app

The Android application entry point. Owns the Application class and wires together the Koin dependency injection graph.

## Ownership

Presentation layer. This module knows about all feature modules. No feature module knows about this module.

## Contents

- `FootballApplication` — Application subclass. Starts Koin and Napier logging in debug builds.
- `MainActivity` — shows the launch screen, then hosts the app inside `FootballTheme` and provides `LocalCrestUrl` and `LocalEmblemUrl` from `NetworkConfig`.
- `AppNavigation` — the single NavHost, wrapped in a scaffold with the bottom bar. A fixture tapped on home opens the Predict tab and predicts it.
- `TopLevelDestination`, `BottomNavBar` — Fixtures, Predict, Assistant and Settings.
- `di/AppModule` — HTTP client, response cache and API service.

## Responsibilities

- Application lifecycle entry point.
- Koin module assembly — the network module is declared here; each feature module declares its own module in `di/`, and the app starts them all.
- The root NavHost and bottom navigation.

## Constraints

- No business logic.
- No direct network calls.
- No ViewModel state.
