# ADR 034 — Storing Question Text for Users Who Opted In

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The consent notice (ADR 022) lets each user choose whether the text of their questions is stored, and the choice is saved as `store_questions`. Nothing stores the text yet: logs only ever hold the question's length (ADR 024). Without the text, the owner can't see which questions the assistant handles badly, so evals and prompts are written from guesses.

## Decision

- **Who:** only signed-in users whose `store_questions` is true. Signed-out questions and users who said no are never stored. Turning the choice off stops future saves straight away, because each request reads the user afresh.
- **What:** one record per question in the account store, collection `questions` (with the usual Firestore prefix, ADR 026): `email`, `asked_at`, `question`, `outcome` (`answered`, `refused`, `strike` or `banned`), `model` and `conversation_id`. The answer is not stored.
- **How long:** `expires_at` is `asked_at` plus 90 days. In Firestore a TTL policy on `expires_at` deletes old records. The policy is set once by hand, an ops step in `docs/plans/hosting-execution-tracker.md` (section 3a). The JSON store is for local use and does not expire records.
- **Where in the code:** `ChatService` saves the record after the answer or the refusal is built, through `AccountService.record_question`.
- **Failure:** a failed save logs a `fallback` event (`store_question` to `question_not_stored`) and never fails the chat.
- **Notice:** its wording ("the text of your questions is stored only if you allow it below") stays accurate, so `CONSENT_VERSION` is not raised and nobody is asked again.

## Consequences

- The owner can read real opted-in questions to find weak answers and write evals.
- The questions collection holds personal data for up to 90 days. A deletion request now covers this collection too.
- Firestore needs a one-off TTL policy. Until it is set, records are kept.
- No new endpoint and no change to the API or the telemetry contract's fields.
