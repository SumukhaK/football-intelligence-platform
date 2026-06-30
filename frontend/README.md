# Frontend

Compose Multiplatform Android-first application for the Football Intelligence Platform.

---

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Kotlin | 2.0.20 | Primary language |
| Compose Multiplatform | 1.7.0 | UI framework (Android-first) |
| Material 3 | via CMP | Design system |
| Koin | 3.5.6 | Dependency injection |
| Ktor Client | 2.3.12 | HTTP client |
| Kotlinx Serialization | 1.7.1 | JSON parsing |
| Kotlinx Coroutines | 1.8.1 | Async and state |
| Coil | 2.7.0 | Image loading |
| Napier | 2.7.1 | KMP-compatible logger |
| Detekt | 1.23.6 | Static analysis |
| Spotless + Ktlint | 6.25.0 / 1.3.1 | Code formatting |
| JUnit 5 | 5.10.3 | Unit testing |
| MockK | 1.13.12 | Mocking |
| Turbine | 1.1.0 | Flow testing |

**Logger choice:** Napier is used instead of Timber because Timber is Android-only. Napier is Kotlin Multiplatform compatible, which preserves the option to add non-Android targets later without changing the logging API.

---

## Architecture

MVVM with Clean Architecture and strict layer separation.

- **ViewModels** own screen state as `StateFlow`. One ViewModel per screen.
- **Composables** are stateless. They receive state and emit events. No business logic inside.
- **Repositories** abstract all network and data access. ViewModels never call the API directly.
- **Navigation** will be handled by a single `NavHost`. Deep links are defined explicitly.
- **UI state** is a sealed class: `Loading`, `Success`, `Error`.

---

## Module Structure

```
:app
 ├── :feature-home
 ├── :feature-prediction
 ├── :feature-match
 ├── :feature-team
 ├── :feature-assistant
 └── :feature-settings
       └── (all features depend on)
             ├── :core-ui
             ├── :core-design-system
             ├── :core-navigation
             ├── :core-model
             ├── :core-network
             └── :core-common

:core-testing  (test dependency only, never shipped)
```

Dependencies flow downward. Feature modules never depend on each other.

---

## Module Responsibilities

| Module | Layer | Purpose |
|---|---|---|
| `:app` | Presentation | Application entry point, DI assembly |
| `:feature-home` | Presentation | Recent matches and upcoming fixtures |
| `:feature-prediction` | Presentation | XGBoost prediction + SHAP explanation display |
| `:feature-match` | Presentation | Match detail and statistics |
| `:feature-team` | Presentation | Team profile and season stats |
| `:feature-assistant` | Presentation | RAG-powered football intelligence chat |
| `:feature-settings` | Presentation | User preferences and developer options |
| `:core-ui` | Presentation | Shared stateless Compose components |
| `:core-design-system` | Presentation | Material 3 tokens, theme, typography |
| `:core-navigation` | Presentation | Route definitions and navigation contracts |
| `:core-model` | Domain | Serializable domain types shared across layers |
| `:core-network` | Infrastructure | Ktor client configuration and base network layer |
| `:core-common` | Infrastructure | Shared utilities, coroutine helpers, base error types |
| `:core-testing` | Test | Test utilities, fakes, and base rules (never shipped) |

---

## Build Instructions

Requires JDK 17+.

```sh
cd frontend

# Build debug APK
./gradlew assembleDebug

# Run all unit tests
./gradlew testDebugUnitTest

# Static analysis
./gradlew detekt

# Check formatting
./gradlew spotlessCheck

# Fix formatting
./gradlew spotlessApply
```

---

## Convention Plugins

Build configuration is shared via convention plugins in `build-logic/`. Modules apply one or more:

| Plugin ID | Applied to |
|---|---|
| `football.android.application` | `:app` only |
| `football.kmp.library` | All library modules |
| `football.android.compose` | Modules using Compose UI |

See [build-logic/README.md](build-logic/README.md).

---

## Development Standards

- TDD required for all ViewModels and repositories. Write the test before the implementation.
- Every Composable has a `@Preview`. No unpreviewable components.
- No hardcoded strings. All user-facing text goes in `strings.xml`.
- All interactive elements have content descriptions for accessibility.
- Coroutines are scoped to ViewModel or lifecycle. No `GlobalScope`.

---

## Future Responsibilities

- Root NavHost and navigation graph (Stage 5).
- Match prediction display with SHAP explanation visualisation.
- Football intelligence assistant chat interface.
- Compose Multiplatform desktop target (after Android is stable).
