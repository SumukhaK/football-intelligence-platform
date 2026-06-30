# :core-navigation

Navigation contracts, route definitions, and navigation utilities.

## Ownership

Presentation layer — infrastructure only. Does not own any screens.

## Future Contents

- `AppDestination` — sealed class or enum of all navigation destinations.
- Navigation extension functions for type-safe route arguments.
- Deep link URI patterns.

## Constraints

- No screen implementations.
- No business logic.
- Feature modules declare their own routes using the contracts defined here.
