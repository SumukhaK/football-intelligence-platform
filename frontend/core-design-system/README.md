# :core-design-system

Material 3 design tokens, typography, colour scheme, and theming for the Football Intelligence Platform.

## Ownership

Presentation layer. All feature modules consume this; nothing depends on feature modules here.

## Contents

- `FootballTheme` — root Compose theme, light and dark.
- `Color.kt` — the brand colour schemes.

## Constraints

- No feature-specific components. Generic design tokens only.
- Every token is named semantically, not by hex value.
- Dark theme support is required from the first implementation.
