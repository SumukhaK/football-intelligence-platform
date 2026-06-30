# :core-network

Ktor HTTP client configuration and base network infrastructure.

## Ownership

Infrastructure layer. Depends on `core-model` for response types.

## Future Contents

- `FootballApiClient` — Ktor client configured with JSON serialization, logging, and retry.
- `ApiConfig` — base URL and timeout configuration.
- `NetworkResult` — typed wrapper for network responses.

## Constraints

- No UI dependencies.
- No business logic. Network plumbing only.
- The Android Ktor engine (`ktor-client-android`) is wired in `androidMain`. Common code uses the multiplatform interface.
