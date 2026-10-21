# ADR 036 — Daily Token Budgets for the Assistant

**Status:** Accepted (21 October 2026)

## Context

The hosted assistant runs on Cloudflare Workers AI, billed per neuron beyond a
free daily allowance (ADR 025). The repository is public and the staging beta
is invite-only, so strangers cannot chat, but any signed-in account, or a
leaked token, could keep the model busy all day. The only throttle was 120
requests a minute per IP. The 8 October guardrail decisions planned one daily
token budget per user, shown as "about N questions left", plus a global
budget, and left staging without them; the owner chose on 21 October to turn
them on in staging too.

## Decision

- Two budgets, in tokens a day: one per signed-in user
  (`ASSISTANT_DAILY_TOKENS_PER_USER`) and one for everyone together
  (`ASSISTANT_DAILY_TOKENS_TOTAL`). Off locally; the server refuses to start on
  Cloud Run with the assistant on and either budget unset. Starting values:
  30,000 per user (about 10 answers) and 900,000 in total (about 300).
- A question starts only if both budgets still cover a typical answer
  (`ASSISTANT_TOKENS_PER_ANSWER`, default 3,000). The answer's reported prompt
  and completion tokens are charged afterwards, so one answer may run slightly
  over and the next is refused; an unreported count is charged as typical.
  Never cut an answer midway.
- Safety refusals and router replies use no model and cost nothing. There is
  no answer cache yet; if one is added, cached answers are free too.
- Usage lives in the account store: Firestore documents
  `<prefix>usage/<day>_<email>` and `<day>_all`, incremented on the server with
  `firestore.Increment` so parallel answers all count, with an `expires_at`
  timestamp two days ahead for a TTL policy. The local JSON store keeps rows
  under its lock. Budgets reset at midnight UTC.
- Chat answers carry `questions_left` and `resets_at`. A refused question gets
  `429 Daily limit reached` with a plain detail, which the app shows as is; the
  app also shows "About N questions left today" under the chat.

## Consequences

- The worst-case daily bill is bounded by the total budget, whatever happens
  to accounts or tokens. Predictions are unaffected.
- Each chat adds two usage reads before the model and up to two writes after.
- Embedding calls are not counted; they are far cheaper than chat.
- Tuning is configuration only. Read real usage from `assistant.answer` logs
  (`prompt_tokens`, `completion_tokens`) before changing the starting values.
- Deploying needs both settings and a TTL policy on `<prefix>usage.expires_at`.
