# :feature-match

Match detail screen showing full match data, statistics, and a link to the prediction for that match.

## Ownership

Presentation layer. Depends on `core-ui`, `core-design-system`, `core-model`, `core-navigation`.

## Future Contents

- `MatchViewModel` — owns `MatchUiState`. TDD required.
- `MatchScreen` — displays full match statistics, lineups (when available), and result.
- `MatchRepository` interface and implementation.

## Constraints

- TDD: ViewModel tests written before implementation.
- No hardcoded strings.
