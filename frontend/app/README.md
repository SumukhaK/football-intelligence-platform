# :app

The Android application entry point. Owns the Application class and wires together the Koin dependency injection graph.

## Ownership

Presentation layer. This module knows about all feature modules. No feature module knows about this module.

## Contents

- `FootballApplication` — Application subclass. Initialises Napier logging in debug builds.

## Responsibilities

- Application lifecycle entry point.
- Koin module assembly — the DI graph is declared here, not in feature modules.
- Root NavHost will be placed here when navigation is wired in Stage 5.

## Constraints

- No business logic.
- No direct network calls.
- No ViewModel state.
