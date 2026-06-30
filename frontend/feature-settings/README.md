# :feature-settings

Application settings screen for user preferences and developer configuration.

## Ownership

Presentation layer. Depends on `core-ui`, `core-design-system`, `core-navigation`.

## Future Contents

- `SettingsViewModel` — owns `SettingsUiState`. TDD required.
- `SettingsScreen` — preference list with toggles for theme, API endpoint, and debug options.
- `SettingsRepository` interface backed by `DataStore`.

## Constraints

- No secrets or API keys in settings state. Endpoint base URL only.
- TDD: ViewModel tests written before implementation.
- No hardcoded strings.
