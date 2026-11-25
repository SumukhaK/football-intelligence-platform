# Streaming contract

**Version:** 1.0.0 (25 November 2026). **Owner:** step ST01 copies it into `docs/api.md` and ADR 037; after ST01 merges, `docs/api.md` is the source of truth and this file points to it.

This is the agreement between the backend lane (ST02 to ST07) and the Android lane (ST08 to ST10). Neither lane may change it on its own. If a step finds the contract is wrong, it stops, explains why in its PR or thread, and a contract change lands first as its own docs PR that bumps the version here and in `docs/api.md`.

The files in [`fixtures/`](fixtures/) are the contract in executable form. The backend's endpoint tests must produce them byte for byte (ST06), and the app's parser tests must read them (ST08). That is what makes the two lanes fit together without a running server.

## 1. Endpoint

| Item | Value |
|---|---|
| Method and path | `POST /v2/assistant/chat/stream` |
| Mounted | Only under `/v2`, with the same consent guard as the other `/v2` data routes. Never under `/v1` or without a prefix (ADR 014). It needs its own router file, because `routers/assistant.py` is also mounted under `/v1`. |
| Request body | Exactly `ChatRequest` from `ai/backend/app/schemas/assistant.py`. No new fields. |
| Request headers | `Authorization: Bearer <token>` as today (optional when accounts are off). `Accept: text/event-stream` is sent by the app but not required. |
| Turned off | Setting `assistant_streaming: bool = True` (env `ASSISTANT_STREAMING`). When false the route is not registered, so the server answers `404`. The app treats `404` as "use `POST /v2/assistant/chat` instead". |

## 2. Errors before the stream starts

Everything that can fail before the first event is a normal HTTP error with the usual `{"error": "...", "detail": "..."}` body and the same status as `POST /v2/assistant/chat` gives today: `401`/`403` from sign-in and consent, `422` from validation, `413` from the body limit, `429` from the rate limiter or the daily budget (ADR 036), `503` when the assistant is not loaded. The safety check, the history check and the budget check all run before the response starts, so they can still return these codes.

## 3. The stream

Status `200`. Headers:

```
Content-Type: text/event-stream; charset=utf-8
Cache-Control: no-cache
X-Accel-Buffering: no
X-Request-ID: <as for every response>
```

Framing follows the server-sent events format. Every event is exactly two lines and a blank line:

```
event: <name>
data: <one line of compact JSON>

```

- Lines end with `\n`. JSON is compact (no spaces after `,` or `:`), UTF-8, not ASCII-escaped. In Python: `json.dumps(payload, separators=(",", ":"), ensure_ascii=False)`; for `done`, `ChatResponse.model_dump_json()`.
- The server sends no `id:`, no `retry:` and no comment lines in 1.0.0. Clients must still ignore comment lines (starting with `:`), `id:` and `retry:` lines, and events with unknown names, so the server can add them later as a minor version.
- A stream ends with exactly one terminal event, `done` or `error`, and then the server closes it. A stream that closes without a terminal event is a network failure for the client.

## 4. Events

| Event | Data | Rules |
|---|---|---|
| `delta` | `{"text":"..."}` | `text` is never empty. It has already passed the stream gate: no `[source: ...]` citation, and on a follow-up no number that no tool returned this turn. Append it to the text shown since the last `reset`. |
| `reset` | `{"reason":"tool_call"}` or `{"reason":"grounding"}` | Throw away all text shown since the start or the last `reset`, and show the waiting state again. `tool_call`: the model decided to call a tool after starting to write. `grounding`: a follow-up answer used a number no tool returned (ADR 030) and is being asked again. Clients must treat an unknown `reason` like any other reset. |
| `done` | The full `ChatResponse` JSON, exactly what `POST /v2/assistant/chat` would return: `answer`, `sources` (always `[]`, ADR 029), `confidence`, `model`, `retrieved_count`, `signature`, `questions_left`, `resets_at` | Terminal. `answer` is the text the app keeps, shows and later sends back as history with `signature`. It equals the `delta` texts since the last `reset` joined together, apart from leading and trailing whitespace. |
| `error` | `{"error":"Assistant not available","detail":"The assistant could not answer just now. Try again."}` | Terminal. The model failed after the stream started. The app shows the same message it shows for a `503` today. |

A refused question (safety, ADR 027) and a fixed router reply (ADR 021) are sent as one `delta` holding the whole text, then `done` (with `model` `safety` or `router`).

## 5. Server duties that clients rely on

1. No `delta` is sent before the history check, the safety check, the budget check, the season router and retrieval with its relevance cut-off have finished.
2. Tool calls run before any `delta` of the answer that uses them. If text was sent before the model asked for a tool, a `reset` comes first.
3. The answer is signed, charged to the budget and stored for an opted-in user (ADR 034) once, when `done` is built.
4. If the client disconnects, the server stops the model call, charges the tokens used so far (prompt tokens plus completion characters divided by 4 when the model reported nothing) and stores the question with outcome `stopped`.
5. `assistant.answer` gains `ttft_ms` (milliseconds from the request to the first `delta`, null when none was sent) and `streamed` (bool). This is telemetry contract 1.2.0 (minor).

## 6. Client duties

1. Show the waiting state until the first `delta`, and again after a `reset`.
2. Never keep text from a stream without a `done`: on `error`, a dropped connection or cancel, replace the partial bubble with the error message.
3. Never send a partial or unsigned answer back as history (the existing `historyWindow` rule).
4. Keep New chat and Send disabled until a terminal event arrives or the stream fails.
5. On `404` from the stream route, call `POST /v2/assistant/chat` for this and later questions in the session.
6. Do not retry a failed stream automatically. It is a POST.

## 7. Fixtures

| File | Scenario |
|---|---|
| [`answer.sse`](fixtures/answer.sse) | First question, model answer in three pieces |
| [`tool_reset.sse`](fixtures/tool_reset.sse) | The model writes, then calls a tool; `reset`, then the answer |
| [`grounding_reset.sse`](fixtures/grounding_reset.sse) | Follow-up whose first try used an ungrounded number; `reset`, then the retried answer |
| [`refusal.sse`](fixtures/refusal.sse) | Safety refusal for a signed-out user who sent no `conversation_id` (so no signature and no budget) |
| [`router.sse`](fixtures/router.sse) | Fixed season-router reply |
| [`error.sse`](fixtures/error.sse) | Model fails after one piece |
| [`truncated.sse`](fixtures/truncated.sse) | Connection drops with no terminal event (client tests only) |

Values in the fixtures are fixed test values: the signature is 64 `a` characters, `resets_at` is `2026-11-26T00:00:00Z`. Backend tests build the same scenario with fakes so the output matches the file exactly.
