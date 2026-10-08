# Accounts and Consent Plan

Status: Proposed, 8 October 2026. Backend first; the Android screens follow once the API exists.
Decisions behind it are recorded in the hosting plan's production AI target and in [hosting-execution-tracker.md](hosting-execution-tracker.md).

## Goal

Only invited people can use the app. Each person agrees to a short notice before anything about their use is recorded. Each person has a stable identity for later steps: the daily token budget in production, strikes and bans, and per-user usage data from the staging beta.

## Decisions

| Topic | Decision |
|---|---|
| Who needs to sign in | The whole app (decided 8 October 2026). Every `/v2` data endpoint needs a session and current consent; `/v2/health`, the docs and the auth routes stay open. After the first sign-in the app asks for a league and team once, kept on the device. |
| Sign-up | Invite-only. The owner creates an invite for an email with a command-line script; there is no public sign-up endpoint. |
| Passwords | The invited person chooses their own password when redeeming the invite, so the owner never knows it. Passwords are hashed with scrypt from the standard library (ADR 022). |
| Sessions | Opaque random tokens, stored hashed, valid for 30 days, revocable. A ban or logout revokes them at once, which is simpler than JWTs for one service. |
| Consent | Versioned notice text. The assistant answers 403 `Consent required` until the user has accepted the current version. Accepting stores the version and the time. Storing question text is a separate opt-in tick box. |
| Strikes and bans | The user record holds a strike count and status (`active` or `banned`). Three strikes means banned for good (the guardrails step adds the strikes). A ban revokes all sessions. |
| Storage | Firestore (free tier) in staging and prod, behind a repository interface. A JSON-file store for local development and tests. This is the project's first database, so it needs an ADR. |
| Switch | `AUTH_REQUIRED` setting: off locally (everything works as today), on in staging and prod. `/v1` and unversioned paths keep working unauthenticated locally only; in the cloud only `/v2` is exposed. |

## Data

- **users:** `email` (lower case, unique), `password_hash`, `status`, `strikes`, `consent_version`, `consented_at`, `store_questions`, `created_at`, `last_login_at`.
- **invites:** `email`, `code_hash`, `expires_at` (7 days), `redeemed_at`.
- **sessions:** `token_hash`, `user_email`, `created_at`, `expires_at`, `revoked`.
- Raw passwords, invite codes and session tokens are never stored or logged, only their hashes.

## API (all under `/v2`)

| Method | Path | Body | Result |
|---|---|---|---|
| POST | `/auth/redeem-invite` | email, invite code, new password | Creates the account and returns a session token |
| POST | `/auth/login` | email, password | Session token |
| POST | `/auth/logout` | (token) | Revokes the session |
| GET | `/me` | (token) | Email, status, whether consent is needed, the current notice text and version, `store_questions` |
| POST | `/me/consent` | notice version, `store_questions` | Records consent |
| any | other `/v2` data routes | unchanged | Need a valid session and current consent when `AUTH_REQUIRED` is on |

Errors use the existing `{ "error", "detail" }` shape: 401 `Not signed in`, 403 `Consent required`, 403 `Account blocked`, 429 `Too many attempts`.

## Security basics

- **Login guessing:** after 5 failed logins for an email within 15 minutes, that email is locked for 15 minutes. Wrong email and wrong password get the same message.
- **Passwords:** minimum 10 characters, hashed with `hashlib.scrypt`, so no new dependency.
- **Invite codes:** 128-bit random, single use, expire after 7 days.
- **Transport:** HTTPS in the cloud (Cloud Run provides it). The app stores the token in Android's encrypted storage.
- **Logs:** no passwords, codes, tokens or question text unless the user opted in.

## Owner tools

- `python -m scripts.create_invite --email friend@example.com` prints a one-time code to send privately.
- `python -m scripts.manage_user --email ... --ban | --unban | --reset-password` for support.

## Build order (each a PR into develop)

1. ADR 022: accounts, sessions and consent. Done; the Firestore store, with `google-cloud-firestore`, comes with the cloud storage step.
2. Repository interface with JSON-file and Firestore implementations; tests against the file store.
3. Account service: invites, password hashing, login lockout, sessions. Unit tests.
4. Auth routes, the `/me` routes and a FastAPI dependency on the `/v2` data routers. Integration tests with `TestClient`. `docs/api.md` updated.
5. Owner scripts.
6. Consent notice text (version 1) and the 403 path. Tests.
7. Android: sign-in, redeem-invite and consent screens, token storage, and handling for 401 and 403 responses (a separate frontend task).

## Open questions

1. What do people see when a session expires after 30 days: sign in again (default), or a longer session?
