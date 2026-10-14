# ADR 030 — Short-Term Chat Memory with Signed History

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The assistant answers each question on its own (ADR 018): `POST /v2/assistant/chat`
takes one message, so follow-ups such as "and the draw?" or "why?" lose their
meaning. The owner tried it on staging and asked for chat memory, and on
15 October 2026 chose the recommended design in the
[chat memory plan](../plans/chat-memory-plan.md).

Constraints:

- **Consent.** The notice (version 2) promises that question text is stored only
  with opt-in, so the server should not keep conversations.
- **Hosting.** Cloud Run scales to zero and may run more than one instance
  (ADR 025), so memory held in one instance's RAM would be lost or split.
- **Cost.** Every history token is paid for again on each model call.
- **Safety.** The history must not be a way around the safety check (ADR 027)
  or the grounding rules (ADR 018).

## Decision

1. **History lives on the phone.** The app keeps the conversation it already
   shows. With each question it sends the last **4 exchanges** as `history`,
   plus a `conversation_id` it generates.
2. **The server signs its answers.** Each response carries a `signature`: an
   HMAC-SHA256 over the user, the conversation ID, the turn number and the
   answer text, keyed by `HISTORY_KEY` (Secret Manager in the cloud). If an
   assistant turn in the history doesn't verify, the server drops the whole
   history and answers the question on its own. User turns need no signature,
   because they are checked again.
3. **Limits, with the oldest turns trimmed first:**
   - at most 4 exchanges and 1,200 history tokens (estimated at 4 characters
     per token)
   - each assistant turn stored as at most 1,500 characters
   - a request body of up to 24 KB (raised from 16 KB)
   - the app starts a new conversation after 30 minutes idle, on New chat, or
     on sign-out
4. **Safety reads the conversation.** Llama Guard gets the user's side of the
   history plus the new question. Only the new question can add a strike.
   Assistant turns are left out, because they are the server's own signed text
   and would make the check dearer.
5. **History is context, never evidence.** The history enters as earlier chat
   turns below the system prompt. A new prompt rule says every number must come
   from a tool called in this turn. Answers are stored without citations
   (ADR 029).
6. **Nothing new is stored.** The server keeps no conversation. Logs gain
   `history_turns`, `history_tokens` and `history_dropped` (counts only). The
   consent notice stays at version 2.
7. **Backward compatible.** `history`, `conversation_id` and `signature` are
   optional. An app that sends no history is answered as before.

## Consequences

- **Cost.** About +32% neurons per answer on average (22 to 29, safety check
  included), and up to +115% at a full window. The free Workers AI allowance
  falls from about 450 to about 345 answers a day.
- **Storage.** No Firestore or server memory. Requests grow by about 1–6 KB.
- **Not covered:** the conversation doesn't follow the user to another phone,
  and it is gone after a reinstall. Option C in the plan (Firestore with
  opt-in) would add that later if it is wanted.
- **Evaluation.** A new multi-turn eval (`evaluation/assistant_conversation.py`)
  covers follow-ups, topic switches, forged turns, injection in the history and
  a harmful request split over turns. Abstention, grounding and season must
  still pass.
- **Router.** The season router still reads only the newest question; a
  follow-up it can't place goes to the model with the history.
