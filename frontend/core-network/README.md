# :core-network

Ktor HTTP client configuration and base network infrastructure.

## Ownership

Infrastructure layer. Depends on `core-model` for response types.

## Contents

- `FootballApiService` / `KtorFootballApiService` — one method per backend endpoint, all under API v2 (ADR 014).
- `CachingFootballApiService` — saves every successful response and replays it when the server can't be reached. Chat is never cached.
- `FileResponseCache` — the on-disk cache in the app's cache directory (`androidMain`).
- `HttpClientFactory` — Ktor client with JSON and timeouts.
- `NetworkConfig` — base URL, API version, and the connect and request timeouts.

## Constraints

- No UI dependencies.
- No business logic. Network plumbing only.
- The Android Ktor engine (`ktor-client-android`) is wired in `androidMain`. Common code uses the multiplatform interface.
