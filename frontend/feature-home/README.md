# :feature-home

Home screen showing recent matches, upcoming fixtures, and entry points to other features.

## Ownership

Presentation layer. Depends on `core-ui`, `core-design-system`, `core-model`, `core-navigation`.

## Future Contents

- `HomeViewModel` — owns `HomeUiState` as `StateFlow`. TDD required.
- `HomeScreen` — stateless Composable. Receives state, emits events.
- `HomeUiState` — sealed class: `Loading`, `Success(matches)`, `Error(message)`.
- `HomeRepository` interface and implementation.

## Constraints

- ViewModel written test-first. No ViewModel without a passing test.
- No direct API calls from the ViewModel. All data goes through the repository.
- No hardcoded strings.
