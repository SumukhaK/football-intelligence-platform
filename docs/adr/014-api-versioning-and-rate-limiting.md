# ADR 014 — Version the API and Add a Rate Limiter

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

Release v1.0.0 (July 2026) shipped an app and an API that served the Premier
League with the original model (`20260630_132617`). Since then the API has
changed shape: five leagues and a `competition` field (ADR 012), a
`draw_possible` flag (ADR 011), fan-friendly explanation labels, `/insights`
and `/competitions`, and a retrained model (ADR 005, ADR 007). Clients built
for v1.0.0 must keep working, and keep getting the answers they were built
against.

The server is open to anything that can reach it and has no authentication
(a non-goal in CLAUDE.md). One runaway client can monopolise the model.

## Decision

1. **Path versions.** `/v2/...` serves the current contract and model.
   `/v1/...` serves the v1.0.0 contract with the original model: Premier
   League only, the original response fields, no `competition` or
   `draw_possible`, no explanation display labels.
2. **Unversioned paths are v1.** `/predict`, `/explain`, `/teams`, `/model`
   and `/health` behave exactly as `/v1/...`, so v1.0.0 clients need no
   change. They are hidden from the OpenAPI docs, which list `/v1` and `/v2`.
3. **Both models are loaded at startup.** The original model uses the same 42
   features, so v1 also gets server-side features (ADR 008). It reports its
   own registry entry on `/v1/model`. `V1_MODEL_PATH` and `V1_MODEL_VERSION`
   choose it.
4. **v2-only endpoints.** `/v2/competitions` and `/v2/insights` exist only in
   v2, because v1 clients never called them. `/health` and `/assistant/chat`
   are the same in both versions.
5. **The app moves to v2.** Its base path becomes `/v2`.
6. **Rate limiting.** A sliding one-minute window per client address,
   `RATE_LIMIT_PER_MINUTE` requests (default 120; `off` disables it). Over
   the limit, the server answers 429 `{"error": "Too many requests", ...}` with
   `Retry-After`. Health checks and the docs are never limited. The limiter
   lives in memory, with no new dependency.

## Alternatives rejected

- **Header or media-type versioning.** It is harder to try in a browser or
  with curl, and the Android client would need custom headers.
- **Unversioned paths as v2.** This would break v1.0.0 clients silently: they
  would get a different model and new fields.
- **`slowapi` or a Redis-backed limiter.** Both add a dependency for a
  single-process local server; the in-memory window is enough.

## Consequences

- Two models stay in memory, about 2 MB more.
- v1 is frozen. New features land in v2 only, and v1 can be retired later
  with a deprecation notice.
- Tests call `/v2/...` for current behaviour and `/v1/...` for the old
  contract.
- The limiter counts per process and per address. Behind a proxy it would
  need the forwarded address, which is out of scope for local use.
