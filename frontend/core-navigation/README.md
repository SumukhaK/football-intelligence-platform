# :core-navigation

Navigation contracts, route definitions, and navigation utilities.

## Ownership

Presentation layer — infrastructure only. Does not own any screens.

## Contents

- `Screen` — sealed class of every route in the app's single NavHost, from `Auth` and `Consent` (ADR 022) through onboarding to the tabs and Settings.

## Constraints

- No screen implementations.
- No business logic.
- Feature modules declare their own routes using the contracts defined here.
