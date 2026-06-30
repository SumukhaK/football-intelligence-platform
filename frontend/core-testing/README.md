# :core-testing

Shared test utilities, fakes, and base classes for unit and integration tests.

## Ownership

Test infrastructure. This module is a `testImplementation` dependency only — it is never shipped in production.

## Future Contents

- `MainDispatcherRule` — JUnit 5 extension to swap `Dispatchers.Main` in tests.
- `FakeNetworkClient` — in-memory Ktor mock client pre-configured for common responses.
- `TestData` — builder functions for domain model test fixtures.
- Turbine flow assertion helpers.

## Constraints

- Only used as a test dependency. Never shipped.
- No production code.
- No Android framework dependencies in `commonMain` test utilities.
