# :core-ui

Reusable Compose UI components shared across feature modules.

## Ownership

Presentation layer — shared components only. Feature-specific UI lives in feature modules.

## Future Contents

- Loading indicators and error state components.
- Shared card, chip, and badge components.
- Image loading components (Coil wrappers).
- Screen-level scaffolds.

## Constraints

- Components must be stateless. They receive state and emit events.
- Every component has a `@Preview`.
- No business logic. No ViewModels.
- No feature-specific code.
