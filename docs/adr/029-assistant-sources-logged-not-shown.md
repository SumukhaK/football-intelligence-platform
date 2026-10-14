# ADR 029 — Assistant Sources Are Logged, Not Shown

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The assistant cites where each fact came from (`[source: tool predict_match]`,
`[source: api.md]`), and the chat response listed the retrieved documents with
excerpts. On staging the owner found both wrong for the app's users: internal
file names such as ADRs and API docs mean nothing to a friend asking about a
match, and the markers break up the answer. The citations still matter for
tracing and for the evals.

## Decision

1. **The model keeps citing.** The prompt's citation rule is unchanged.
2. **The server strips them before replying.** `POST /v2/assistant/chat`
   returns the answer without `[source: ...]` markers and with `sources: []`.
   The response shape is unchanged, so older apps keep working; the app
   already hides the sources card and the confidence when `sources` is empty.
3. **The logs keep them.** `assistant.answer` gains two optional attributes:
   `sources`, the retrieved document names, and `cited`, what the answer cited.
   Neither contains the question or the answer text (ADR 022).

## Consequences

- **Easier:** answers read cleanly, and no internal document names reach users.
- **Traceability moves to the logs.** Checking why an answer said something
  means reading its `assistant.answer` line by request ID.
- **API contract:** `sources` is now always empty; `docs/api.md` says so. A
  later version can drop the field.
