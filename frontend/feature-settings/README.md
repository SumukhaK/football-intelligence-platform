# :feature-settings

Settings: backend status, model information and About.

## Ownership

Presentation layer. Depends on `core-ui`, `core-design-system`, `core-navigation`.

## Contents

- `SettingsScreen` — the backend status card (passed in by the app) and links to Model Info and About.
- `SettingsViewModel`, `ModelInfoScreen` — model version, dataset version and the metrics recorded for it in the model registry.
- `AboutScreen` — app and project information.
- `ModelInfoRepository` — reads `GET /v2/model`.

## Constraints

- No secrets or API keys in settings state. Endpoint base URL only.
- TDD: ViewModel tests written before implementation.
- No hardcoded strings.
