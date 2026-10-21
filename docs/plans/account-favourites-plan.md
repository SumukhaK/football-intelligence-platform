# Account Favourites Implementation Plan

> Agentic workers: use subagent-driven-development or executing-plans. Preserve unrelated work.

**Goal:** Retain each authenticated account's validated league/team across installs.

**Architecture:** Extend the existing JSON/Firestore account records and authenticated
API. Hydrate the existing synchronous favourite cache from a guarded server
repository, then let a navigation gate select onboarding or home.

**Tech Stack:** FastAPI/Pydantic, existing account adapters, Kotlin/Compose/Ktor/Koin.

**Spec:** [ADR 035](../adr/035-server-account-favourites.md), extending ADRs 022, 023, 026 and 031.

## Global Constraints

- No new database, authentication system, dependency, staging writes or deployment.
- Canonical league/team names and membership come from the existing served catalog.
- No empty fallback on network, provider or invalid-data errors.
- Account identity comes from credentials; cache is never a source of server writes.
- No file over 400 lines; resource strings, MVVM and existing UI patterns apply.

## Task 1 — Backend persistence and authenticated contract

Ownership: `ai/` source/tests and `docs/api.md` only.

- [x] Write failing storage and API tests: legacy/fresh empty, persisted read/write,
  field preservation including stale auth writes, canonical league/team membership,
  malformed input/storage, unauthenticated/account isolation and provider failure.
- [x] Add optional favourite and narrow atomic/merge updates to both account stores.
- [x] Implement GET/PUT `/v2/me/preferences` returning `{email, favourite}`;
  PUT body is `{favourite: {league, team}}`. No client account identifier is accepted.
- [x] Run focused tests and backend checks; record actual results and API docs.

## Task 2 — Mobile repository, cache, save flow and navigation gate

Ownership: `frontend/` only.

- [x] Write failing API/repository/cache/ViewModel tests for server authority,
  retry, successful null, failed save, account switching and delayed responses.
- [x] Add serializable preference DTOs and explicit session-token-bound GET/PUT.
- [x] Scope confirmed cache entries by server email; reject unbound or replaced
  sessions and discard legacy unscoped keys without uploading them.
- [x] Add loading/loaded/confirmed-empty/error states after consent, then route.
- [x] Make the existing picker save remotely, show errors and complete only on success.
- [x] Run affected tests, static checks and available Android build tasks.

## Task 3 — Review and verification

- [x] Review both tasks for spec compliance and account isolation.
- [x] Represent reinstall/upgrade with a new empty local cache and persisted account.
- [x] Run broader offline checks supported by this environment; record commands,
  results and limitations in `docs/reports/account-favourites-verification.md`.
- [x] Report changed scope and exact Git state; no merge, release or deployment.

## Review Focus

Delayed saves must use the originating token even if another account signs in.
Stale whole-account writes must preserve the latest favourite. Invalid stored
preferences must fail visibly. A cancelled request must not become a successful
empty account. Recreated cache instances must recover from server storage.
