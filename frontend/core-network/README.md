# :core-network

Ktor HTTP client configuration and base network infrastructure.

## Ownership

Infrastructure layer. Depends on `core-model` for response types.

## Contents

- `FootballApiService` / `KtorFootballApiService` — one method per backend endpoint, all under API v2 (ADR 014).
- `CachingFootballApiService` — saves supported successful data responses and replays it when the server can't be reached. Chat is never cached.
- `FileResponseCache` — the on-disk cache in the app's cache directory (`androidMain`).
- `AuthApiService` — sign-in, redeem invite, sign out, `GET /v2/me` and consent (ADR 022). Never cached.
- `AuthSession`, `bearerAuth` — the session token as a `StateFlow`, and a Ktor plugin that sends it as `Authorization: Bearer <token>` on every request and signs out when the server answers 401 for it.
- `HttpClientFactory` — Ktor client with JSON, timeouts, GET retries and the session token. Debug logging skips the `/auth/` routes so passwords and tokens stay out of logcat.
- `installGetRetry` — retries GET requests up to twice on 429, 502, 503 and 504 with capped backoff and jitter, honouring a `Retry-After` of up to 8 s. A non-JSON 429 from the platform can also retry a POST during cold start; backend JSON POST errors and connection failures are not retried.
- `NetworkConfig` — base URL (set per build flavor by the app), API version, the connect and request timeouts, and `crestUrl` / `emblemUrl` for team crest and league emblem images (ADR 020).

## Constraints

- No UI dependencies.
- No business logic. Network plumbing only.
- The Android Ktor engine (`ktor-client-android`) is wired in `androidMain`. Common code uses the multiplatform interface.
