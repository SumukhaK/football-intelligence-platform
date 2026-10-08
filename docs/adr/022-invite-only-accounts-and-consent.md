# ADR 022 — Invite-Only Accounts, Sessions and Consent

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The app will be hosted for family and friends, with a closed beta on staging
first ([hosting plan](../plans/hosting-plans.md)). The assistant's inference is
metered, usage data from the beta sets production limits, and harmful use leads
to a ban. All of that needs a stable identity per person, and people must agree
to what is recorded. Until now the API had no users at all (a non-goal in
`.claude/CLAUDE.md` for the early stages, which this ADR ends for hosted
deployments).

Decisions already made with the owner
([accounts plan](../plans/accounts-and-consent-plan.md)): invite-only email and
password accounts, the whole app behind sign-in, a consent notice after the
first sign-in, and question text stored only on opt-in.

## Decision

1. **Invites.** The owner creates an invite for an email with
   `python -m scripts.manage_accounts invite`. The person redeems the one-time
   code with a password of their choosing, so the owner never knows it. There
   is no public sign-up. Codes expire after 7 days.
2. **Passwords** are hashed with scrypt from the standard library
   (`hashlib.scrypt`, n=2^14, r=8, p=1, 16-byte salt), compared in constant
   time. No new dependency is added. Minimum length is 10 characters.
3. **Sessions** are random 256-bit opaque tokens, sent as
   `Authorization: Bearer`, stored only as SHA-256 hashes, and valid for 30
   days. A logout or a ban revokes them at once, which JWTs can't do without
   extra state.
4. **Lockout.** After 5 failed logins for an email within 15 minutes, logins
   for that email are refused for 15 minutes. Wrong email and wrong password
   get the same message.
5. **Consent.** A versioned notice (`backend/app/consent.py`). Data routes
   answer 403 `Consent required` until the user accepts the current version.
   Acceptance stores the version, the time and the `store_questions` choice.
6. **Scope.** With `AUTH_REQUIRED=true`, every `/v2` data route needs a
   session and current consent. `/v2/health`, the docs, the auth routes and
   the crest and emblem redirects (ADR 020; image loaders send no token)
   stay open. `/v1` and unversioned paths are not mounted at all, because
   leaving them open would bypass sign-in. `AUTH_REQUIRED` is off by default,
   so local development works as before.
7. **Storage.** An `AccountStore` interface. This change ships a JSON-file
   store (one file, atomic writes, a process lock) for local use, tests and a
   single-instance staging service. A Firestore store follows with the cloud
   storage step of the hosting tracker, under the same interface.
8. **Bans.** A user record has a `status` and a strike count. Banned users get
   403 `Account blocked` and lose their sessions. Strikes are added by the
   guardrails step.

## Consequences

- The Android app needs sign-in, redeem-invite and consent screens and must
  send the token. That is a separate frontend task.
- The JSON-file store suits one process. Several Cloud Run instances need the
  Firestore store first.
- The v1 contract (ADR 014) is unavailable wherever sign-in is on. Old v1.0.0
  app builds therefore don't work against hosted servers; they were never
  distributed.
- Raw passwords, invite codes and tokens are never stored or logged.
