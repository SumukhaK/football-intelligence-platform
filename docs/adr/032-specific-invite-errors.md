# ADR 032 — Specific Errors for Used and Expired Invites

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

ADR 022 answered every failed invite redeem with `400 Invalid invite`, so nobody could probe which emails had accounts. On 15 October 2026 a friend's sign-up succeeded on the server while his app timed out on a cold start, and each retry then said the code was "wrong, used or expired". He couldn't tell that his account already existed.

## Decision

- **The right code, already used:** `409 Invite already used`. The detail says to sign in, or to ask for a new code to reset the password.
- **The right code, past 7 days:** `410 Invite expired`.
- **No invite, or a wrong code:** `400 Invalid invite`, as before.

The code is checked first, so only someone holding the right code learns more than "invalid". The app shows each case in its own words.

## Consequences

- Friends who retry after a timeout are told to sign in instead.
- `auth.event` gains the outcomes `invite_used` and `invite_expired`.
- Older apps show their usual invite error for 409 and 410.
