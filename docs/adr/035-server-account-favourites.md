# ADR 035 — Server Account Favourites

**Status:** Accepted (implementation authorized 19 October 2026)

## Context

ADR 023 keeps the favourite on a phone; ADR 031 sends it with chat questions.
Uninstalling loses it and another sign-in can inherit it. ADR 026 already stores
accounts in Firestore in staging and JSON locally, superseding the earlier
file-only backend standard for accounts. This change reuses that account store.

## Decision

- Add an optional `favourite` object (`league`, `team`) to existing user records.
  Missing fields mean confirmed empty; malformed stored values are errors.
- Add authenticated `GET /v2/me/preferences` and `PUT /v2/me/preferences`.
  Both return `{email, favourite}`; PUT accepts `{favourite: {league, team}}`.
  Identity comes exclusively from the bearer session. League and team use the
  canonical names from the supported competitions and latest-season teams API.
- Reject invalid writes with structured 422 errors; provider failures return
  structured 503 errors. An empty favourite is only a successful explicit null.
- Patch only the favourite field. Preserve unrelated account fields and prevent
  stale authentication/consent writes from undoing a preference change.
- After consent, Android loads server preferences before choosing home or
  onboarding. Loading and failures never select onboarding; failures offer retry.
  A non-saveable navigation lifetime prevents an old feature screen restoring
  before the account cache is confirmed after Activity/process recreation.
- Save the picker selection on the server before completing or relaunching.
  Cache only confirmed responses under the stable server account identity.
  Isolate cache access by the current session and reject late session responses.
  Discard legacy unscoped preferences; never upload them automatically.

## Consequences

The same account recovers its favourite with an empty cache after reinstall or
upgrade. Fresh and legacy accounts without fields choose once. Startup requires
a successful server read. Older apps keep their existing API behavior; they do
not automatically gain server persistence. No new dependency or cloud migration
is required. Tests use temporary JSON and fake Firestore, never live accounts.
Activity recreation resets navigation through the account checks, including
the current tab. Device process death and physical reinstall remain manual checks.
