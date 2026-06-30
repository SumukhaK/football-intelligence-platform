# Frontend

Compose Multiplatform Android-first application for the Football Intelligence Platform.

---

## Ownership

Frontend implementation. Follows the standards defined in `.claude/CLAUDE.md` section 7.

---

## Architecture

MVVM with strict layer separation.

- **ViewModels** own screen state as `StateFlow`. One ViewModel per screen.
- **Composables** are stateless. They receive state and emit events. No business logic.
- **Repositories** abstract all network and data access. ViewModels never call the API directly.
- **Navigation** is handled by a single `NavHost`. Deep links are defined explicitly.
- **UI state** is a sealed class: `Loading`, `Success`, `Error`.

---

## Directory Structure (planned)

```
frontend/
  app/
    src/
      main/
        kotlin/
          com/footballintelligence/
            ui/           # Screens and Composables
            viewmodel/    # ViewModels and UI state
            repository/   # Repository interfaces and implementations
            navigation/   # NavHost and route definitions
            domain/       # Domain models used by the UI layer
        res/
          values/
            strings.xml   # All user-facing strings
  build.gradle.kts
```

---

## Development Standards

- TDD required for all ViewModels and repositories. Write the test before the implementation.
- Every Composable has a `@Preview`. No unpreviewable components.
- No hardcoded strings. All user-facing text goes in `strings.xml`.
- All interactive elements have content descriptions for accessibility.
- Coroutines are scoped to ViewModel or lifecycle. No `GlobalScope`.

---

## Future Responsibilities

- Match prediction display with SHAP explanation visualisation.
- Football intelligence assistant chat interface.
- Data browsing: match history, player stats, league standings.
- Offline-capable data caching.
- Compose Multiplatform desktop target (after Android is stable).
