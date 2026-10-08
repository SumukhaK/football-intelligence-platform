# :app

The Android application entry point. Owns the Application class and wires together the Koin dependency injection graph.

## Ownership

Presentation layer. This module knows about all feature modules. No feature module knows about this module.

## Contents

- `FootballApplication` — Application subclass. Starts Koin and Napier logging in debug builds.
- `MainActivity` — shows the launch screen, then hosts the app inside `FootballTheme`, provides `LocalCrestUrl` and `LocalEmblemUrl` from `NetworkConfig`, and passes whether a session token is held.
- `AppNavigation` — the single NavHost, wrapped in a scaffold with the bottom bar. It starts at sign-in without a session, else at the notice check, then onboarding (first launch) or Fixtures. A fixture tapped on home opens the Predict tab and predicts it.
- `AuthRoutes` — the sign-in and notice routes, drawn edge to edge, and `FollowSession`, which returns to sign-in from any screen when the session ends (sign out or a 401) (ADR 022).
- `TeamPickerRoute` — the favourite team picker, for onboarding and from Settings.
- `TopLevelDestination`, `BottomNavBar` — Fixtures, Predict, My Team and Assistant.
- `di/AppModule` — the session, HTTP client, response cache, API service and auth API.

## Responsibilities

- Application lifecycle entry point.
- Koin module assembly — the network module is declared here; each feature module declares its own module in `di/`, and the app starts them all.
- The root NavHost and bottom navigation.

## Constraints

- No business logic.
- No direct network calls.
- No ViewModel state.
