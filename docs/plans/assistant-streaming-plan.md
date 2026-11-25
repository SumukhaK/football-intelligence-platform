# Assistant streaming plan

**Status:** Proposed 25 November 2026. Not started. Needs ADR 037 before any code.
**Roadmap entry:** [Stream assistant answers token by token](../roadmap/future-improvements.md#stream-assistant-answers-token-by-token)
**Ships in:** a minor release of its own (backend and app together).

Today the assistant writes the whole answer before the app shows anything. On staging (v2.6.3) the first text appears after p50 2,835 ms and p95 6,064 ms, while the model's own time to first token, streamed, is p50 486 ms and p95 1,280 ms ([Release metrics](../../README.md#release-metrics)). Streaming sends the answer to the phone as it is written, so the user starts reading sooner. The answer itself, and every guardrail, stay the same.

## 1. What does not change

These run before the first word is sent, exactly as today:

| Step | Where | Streaming effect |
|---|---|---|
| Sign-in, request size, rate limit | middleware | None. A failure is still a normal HTTP error with JSON. |
| History signature check (ADR 030) | `ChatService._checked_history` | None. |
| Safety check and strikes (ADR 027) | `ChatService._respond` | None. A refusal is sent as one piece, not streamed. |
| Daily token budget check (ADR 036) | `AssistantBudget.check` | None. A used-up budget is still HTTP 429. |
| Season router (ADR 021) | `AssistantService._route` | A fixed router reply is sent as one piece. |
| Retrieval and the relevance cut-off (ADR 025) | `AssistantService._retrieve`, `build_messages` | None. The cut-off decides the prompt before the model starts. |
| Tool-call rounds (ADR 018) | `AssistantService._answer` | Tool rounds still run in full before any answer text is sent. |

The non-streaming `POST /v2/assistant/chat` stays as it is. Evals, scripts and older app versions keep using it.

## 2. Backend changes

### 2.1 Model adapters stream (`ai/assistant/generation/generator.py`, `ai/assistant/workers_ai.py`)

- Add a `StreamingGenerator` protocol next to `ToolCallingGenerator`: `chat_stream(messages, tools)` yields text pieces, tool calls, and a final usage record (prompt and completion tokens, cost).
- Ollama: `client.chat(..., stream=True)`. Ollama returns tool calls in streamed chunks and token counts in the last chunk.
- Workers AI: `"stream": true` on `chat/completions`, read the server-sent events with `httpx.stream`. Tool-call arguments arrive in pieces and are joined before they are parsed. Ask for usage in the last event (`stream_options.include_usage`).
- Retry (ADR 024's policy) only before the first piece arrives. After that, a broken stream is an error, never a silent retry, because the user has already seen text.

### 2.2 Which text may go out (`ai/assistant/services/`)

A new `StreamGate` class (its own file, to keep `assistant_service.py` under 400 lines) sits between the model and the phone. It holds back text until it is safe to send:

1. **Tool round or answer?** Each model call is streamed. Text is only sent once the call has produced real text and no tool call. If a tool call arrives after some text was sent, the gate sends a `reset` event, the app clears the bubble, and the tools run as today.
2. **Citations.** `[source: ...]` is held back until it closes and is removed, as `strip_citations` does today (ADR 029).
3. **Grounding on follow-ups (ADR 030).** Today a follow-up answer with a number that no tool returned this turn is asked for again once. With streaming, each number is held until it is complete and is checked against this turn's tool results before it is sent. If it fails, the gate sends `reset` and runs the same single retry, streamed. An invented number never reaches the screen.

The routed path, the refusal and the `I don't have enough information` answer go through the same code, so the app has one way to read every answer.

### 2.3 The endpoint (`ai/backend/app/routers/assistant.py`, `chat_service.py`)

`POST /v2/assistant/chat/stream`, same `ChatRequest` body, reply `text/event-stream`:

| Event | Data | When |
|---|---|---|
| `delta` | `{"text": "..."}` | Each piece of answer text that passed the gate |
| `reset` | `{}` | Throw away the text so far (a late tool call or a failed grounding check) |
| `done` | The full `ChatResponse`: `answer`, `model`, `confidence`, `signature`, `questions_left`, `resets_at` | Last event of a good answer. `answer` is the final text the app keeps. |
| `error` | `{"error": "...", "detail": "..."}` | The model failed after the stream started |

- Anything that fails before the first event (401, 422, 429, 503) is a normal JSON error, so the app's current error handling still works.
- The answer is signed (ADR 030), charged to the budget (ADR 036) and stored for opted-in users (ADR 034) once, when the stream ends.
- If the phone disconnects, the server stops the model call, charges the tokens used so far (estimated from text length where the model gave no count) and stores the question with a new outcome, `stopped`.
- Headers `Cache-Control: no-cache` and `X-Accel-Buffering: no` so Cloud Run and proxies pass pieces straight through.
- A setting `ASSISTANT_STREAMING` (pydantic-settings, on by default) turns the endpoint off; it then answers 404 and the app falls back.
- Telemetry: `assistant.answer` gains `ttft_ms` (time to the first `delta`) and `streamed`. That is a minor bump of the telemetry contract (ADR 024); the dashboard can chart it later as its own task.

### 2.4 Backend tests

- Adapters: streamed text, streamed tool calls, usage in the last chunk, retry only before the first piece.
- `StreamGate`: text then late tool call gives `reset`; citations removed across piece boundaries; an ungrounded number on a follow-up never leaves the gate; a grounded one does.
- `ChatService`: refusal, router reply, budget 429 before the stream, signature and budget charge once at the end, disconnect charges and records `stopped`.
- Endpoint integration tests with `TestClient`, including the request ID on log lines written while streaming.
- Evals: run the grounding and "I don't know" evals through the streaming path too; the joined `delta` text must equal `done.answer`, and scores must match the non-streaming path.

## 3. Android changes

The app needs code changes in four modules. Ktor stays at 2.3.13: the stream is read line by line with `bodyAsChannel()`, so no new dependency is needed.

| Module | Change |
|---|---|
| `core-model` | `ChatStreamEvent` sealed class: `Delta`, `Reset`, `Done(ChatResponse)`, `Failed`. `ChatMessage` gains `isStreaming`. |
| `core-network` | `FootballApiService.chatStream(request): Flow<ChatStreamEvent>`, reading the server-sent events. Never retried (it is a POST). A 404 tells the caller to fall back. `CachingFootballApiService` passes it through. |
| `feature-assistant` repository | `AssistantRepository.chatStream(...)`; falls back to `chat(...)` when the stream endpoint is missing or the setting is off. |
| `feature-assistant` ViewModel | Adds an empty assistant bubble, appends each `Delta`, clears it on `Reset`, and on `Done` replaces it with the final signed answer and updates questions left. An error mid-answer turns the bubble into the error message. Leaving the screen cancels the stream. |
| `feature-assistant` screen | The bubble grows as text arrives; the typing dots show only until the first word; the list keeps scrolling as the last bubble grows; screen readers announce the answer once, when it is done. New strings in `composeResources`; a `@Preview` of a bubble mid-answer. |

Two rules carry over from chat memory (ADR 030): a half-finished or unsigned answer is never sent back as history (`historyWindow` already skips answers without a signature), and New chat stays disabled while an answer is arriving.

Tests are written first (ViewModel and repository TDD): text building up, `reset`, `done` with signature and questions left, an error mid-answer, cancel, and the fallback to the old endpoint. The network reader is tested with Ktor's `MockEngine` and a streamed body.

## 4. Effort

Days are focused working days for one engineer, including tests and docs.

| # | Pull request | Area | Days |
|---|---|---|---|
| 0 | Spike: check Workers AI streams tool calls and usage for the hosted model, and that Cloud Run passes events through unbuffered | Backend | 0.5 |
| 1 | ADR 037, `docs/api.md`, telemetry contract bump | Docs | 0.5 |
| 2 | Streaming in the Ollama and Workers AI adapters | Backend | 1–1.5 |
| 3 | `StreamGate`, streaming in `AssistantService`, the endpoint, budget, signature and disconnect handling, evals | Backend | 3–4 |
| 4 | Network reader, repository and ViewModel (TDD) | Android | 1.5–2 |
| 5 | Chat screen, strings, previews, accessibility, fallback | Android | 1.5–2 |
| 6 | Staging check (time to first word on real traffic), README metrics, changelog | Release | 0.5 |
| | **Total** | | **about 9–11 days** |

Backend is about 5–6.5 days, Android about 3–4 days. Each row is one pull request into `develop`, in this order; the app work (rows 4–5) can start once row 1 fixes the event format.

## 5. Risks

| Risk | What we do |
|---|---|
| The hosted model may not stream tool calls well | The spike (row 0) checks it first. Fallback: run tool rounds without streaming and stream only the final answer call. |
| Safety check, retrieval and tool rounds still come before the first word | Expect a smaller gain on tool questions than the 486 ms model figure. Row 6 measures the real time to first word. |
| A `reset` looks jumpy | Rare: it happens only on a late tool call or a failed grounding check. `assistant.answer` logs how often. |
| Text arriving many times a second makes the screen redraw too often | The ViewModel batches updates (about every 50 ms). |
| Old app versions | They keep calling `POST /v2/assistant/chat`, which does not change. |

Out of scope: a Stop button, streaming in the web pages, and any change to prompts or models.
