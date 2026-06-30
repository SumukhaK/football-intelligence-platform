# :feature-team

Team profile screen showing squad, season stats, and recent match history.

## Ownership

Presentation layer. Depends on `core-ui`, `core-design-system`, `core-model`, `core-navigation`.

## Future Contents

- `TeamViewModel` — owns `TeamUiState`. TDD required.
- `TeamScreen` — displays team information and match history.
- `TeamRepository` interface and implementation.

## Constraints

- TDD: ViewModel tests written before implementation.
- No hardcoded strings.
