# :core-testing

Shared test utilities, fakes, and base classes for unit and integration tests.

## Ownership

Test infrastructure. This module is a `testImplementation` dependency only — it is never shipped in production.

## Status

Empty. Test helpers currently live next to the tests that use them. No module depends on this one.

## Constraints

- Only used as a test dependency. Never shipped.
- No production code.
- No Android framework dependencies in `commonMain` test utilities.
