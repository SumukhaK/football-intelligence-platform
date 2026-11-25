# ST06: The streaming endpoint

Branch: `feature/streaming-st06-endpoint` · PR into `develop` · PR title: `feat(backend): add the streaming assistant chat endpoint`

**Needs:** ST05 · **Effort:** 1–1.5 days · **Lane:** Backend

## Goal

`POST /v2/assistant/chat/stream` exactly as `../contract.md` says, with the safety check, history check and budget check before the stream, and signing, budget charge and question storage once at the end.

Done when: the endpoint's output for each fixture scenario equals the file in `../fixtures/` byte for byte; every server duty in contract section 5 has a test; `POST /v2/assistant/chat` and `/v1` are unchanged.

## Files you own

New `ai/backend/app/routers/assistant_stream.py`, new `ai/backend/app/services/chat_stream_service.py`, new `ai/backend/app/utils/sse.py`, `ai/backend/app/services/chat_service.py` (only to share its checks), `ai/backend/app/routing.py`, `ai/backend/app/loaders.py`, `ai/backend/app/config.py`, `ai/backend/app/services/account_store.py` (the `stopped` outcome comment), `ai/.env.example`, `docs/api.md` (only if behaviour differs from ST01's text: then stop and raise it), their tests, this step's tracker row.

## Read first

`../contract.md` (all), `../fixtures/`, `ai/backend/app/routers/assistant.py`, `ai/backend/app/services/chat_service.py`, `ai/backend/app/routing.py` (note `assistant.router` is also mounted under `/v1`), `ai/backend/app/loaders.py`, `ai/backend/app/exceptions/`, `ai/tests/backend/test_assistant_endpoint.py`, `test_chat_safety.py`, `test_assistant_budget.py`, `test_chat_history.py`, ST00's answer 5.

## Design (follow it)

- **Share the checks.** Split `ChatService._respond` so its pre-checks (history, safety with strikes, budget check) are a public `precheck(request, user) -> Precheck` returning either a refusal `ChatResponse` with its outcome, or the checked history. `chat()` keeps its behaviour and tests.
- **`ChatStreamService.stream(request, user) -> Iterator[ChatStreamEvent]`** (`ChatStreamEvent` is `SseDelta | SseReset | SseDone | SseError` dataclasses in `utils/sse.py`). It calls `precheck` first; the route calls it before building the response, so a 401/403/422/429/503 is a normal JSON error. A refusal becomes one `SseDelta` and `SseDone`. Otherwise it maps `Delta`/`Reset`/`Final` from `StreamingAnswerer.answer(with_favourite(request), history)`; on `Final` it builds the `ChatResponse` exactly as `_respond` does (`strip_citations`, `sources=[]`), settles the budget, signs (`_signed`) and stores the question (`answered`), then yields `SseDone`.
- **Errors after the first event:** log the exception type as `chat()` does and yield `SseError` with the contract's text. Charge tokens used so far.
- **Disconnect:** a `finally` that runs when the iterator is closed before `Final`: close the answerer, charge prompt tokens plus completion characters divided by 4 when the model reported nothing, store the question with outcome `stopped`. Prove with a test that closes the iterator after the first event.
- **`utils/sse.py`:** `format_event(event) -> str` producing the exact framing in contract section 3; JSON with `separators=(",", ":")` and `ensure_ascii=False`; `done` uses `ChatResponse.model_dump_json()`.
- **Route** in its own router `assistant_stream.py`, a plain `def` like `chat` (FastAPI runs the pre-check in the thread pool), returning `StreamingResponse(iterator, media_type="text/event-stream; charset=utf-8", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})`. OpenAPI docstring and summary. Include it only in the `/v2` data routers with the consent guard, and only when `settings.assistant_streaming` is true.
- **Loader:** build `ChatStreamService` next to `ChatService` in `loaders.py` and keep it on `app.state.chat_stream_service`; 503 when missing, as `_get_chat_service` does.
- **Setting:** `assistant_streaming: bool = True` in `Settings`, documented in `ai/.env.example`.

## Tests to write first

- `ai/tests/backend/test_sse.py`: framing, compact JSON, non-ASCII text kept, `done` equals `model_dump_json()`.
- `ai/tests/backend/test_assistant_stream_endpoint.py` with `TestClient` and fakes: one test per fixture except `truncated.sse`, comparing the body to the file byte for byte; headers; 422 on an empty message; 429 when the budget is used up (no stream started); 401/403 with accounts on; 503 when not loaded; 404 when `assistant_streaming=False`; `/v1/assistant/chat/stream` and `/assistant/chat/stream` are 404; the request ID appears on every log line written while streaming.
- `ai/tests/backend/test_chat_stream_service.py`: budget charged once and signature only on `done`; question stored once with `answered`; refusal adds a strike exactly as `chat()` does; closing after the first event charges and stores `stopped`; an error mid-stream yields `SseError`, charges what was used and returns no provider text.
- Existing `test_assistant_endpoint.py`, `test_chat_safety.py` and `test_chat_history.py` stay green unchanged.

## Verify by hand

Run the backend with Ollama (`uv run uvicorn backend.app.main:app`), then `curl -N -X POST localhost:8000/v2/assistant/chat/stream -H 'Content-Type: application/json' -d '{"message":"What does the model predict for Arsenal v Chelsea?"}'`. Paste the events with the time each arrived. Repeat with Ctrl+C after the first event and show the `stopped` log line.

## Docs to update

`docs/api.md` only if ST01's text needs a correction (then stop and raise it first), `ai/backend/README.md` (routers and services list), `README.md` setting table if it lists settings, this step's tracker row.

## Reviewer checklist

- [ ] All six non-truncated fixtures matched byte for byte.
- [ ] Every duty in contract section 5 has a test.
- [ ] Stream route absent from `/v1` and unprefixed paths; consent guard applied.
- [ ] `chat()` behaviour and its tests unchanged.
- [ ] No question or answer text in any log line.

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b feature/streaming-st06-endpoint`. If your environment assigns a branch name, use that instead and say so in the PR.
4. **Red.** Write the tests listed under *Tests to write first*. Run them and see each fail for the reason you expect (missing function, wrong value), not from a typo or an import error. Commit them first: `test(backend): ...`. Paste the failing summary line into the PR under **Red**.
5. **Green.** Write the least code that makes them pass. Then refactor with the tests green. Commit as `feat(backend): ...`.
6. Run every command under *Commands that must pass*. Paste each final summary line into the PR under **Commands**.
7. Do the *Verify by hand* check and write what you saw in the PR under **Manual check**.
8. Update the docs listed in the step, and this step's row and section in `../tracker.md`: status `Done (YYYY-MM-DD)`, ticked boxes, and the evidence links.
9. Open the PR into `develop` (never `main`) with the title given above and these sections: Summary, Red, Green, Commands, Manual check, Docs, New dependencies (say "None" or name each one and its ADR), Reviewer checklist (copy the step's list and tick it yourself).
10. Stop. Do not start the next step. Hand the PR to a reviewer with [`../review.md`](../review.md).

Never: skip, delete, weaken or mark as expected-failure an existing test to get green; change [`../contract.md`](../contract.md) or the fixtures (stop and raise it instead); touch files outside **Files you own** unless the step says so; leave a `TODO` without a linked issue; commit commented-out code; log the user's question or answer text.

## Python rules (from `.claude/CLAUDE.md`; apply to every file you write)

- Work in `ai/`. Python 3.12 with `uv`. Black (88 columns), Ruff, mypy strict.
- Type annotations on every function signature. Every public module, class and function has a one-line docstring.
- No file over 400 lines and no function over 40 lines. `ai/assistant/services/assistant_service.py` is already at the limit: add nothing to it unless the step says so.
- One concern per function; if its name needs "and", split it. No wildcard imports, no mutable default arguments, no global mutable state.
- Settings only through `ai/backend/app/config.py` (`Settings`, pydantic-settings) or `ai/assistant/configuration.py`; never read `os.environ` directly. Every new setting goes in `ai/.env.example` with a comment.
- Layering: `shared/` imports nothing from `assistant/` or `backend/`; `assistant/` never imports `backend/`. Routes stay thin; logic lives in services.
- Errors to clients keep the `{"error": ..., "detail": ...}` shape. Provider errors are logged by type only, never returned (they can name local URLs).
- Telemetry goes through `shared.telemetry.events.emit` with an `EventName`; never log question or answer text (ADR 022, ADR 034).
- Tests mirror source: `ai/assistant/x/y.py` is tested in `ai/tests/assistant/test_y.py` (or the matching sub-folder), backend code in `ai/tests/backend/`. Tests are deterministic: inject clocks and sleep functions, no network, no real model. Fakes live next to the tests that use them.
- Coverage stays at or above `fail_under` in `ai/pyproject.toml`.
- A new dependency needs an ADR and a line in the PR description. This feature needs none: `httpx` and `ollama` already stream.
- Conventional Commits: `type(scope): description`, lowercase, imperative, no full stop. Scopes `backend`, `ai`, `docs`.

## Commands that must pass (from `ai/`)

```bash
uv sync --extra dev
uv run ruff check .
uv run black --check .
uv run mypy .
uv run pytest --cov --cov-report=term-missing
```

While fixing a failure, re-run only the failing tests (`uv run pytest path::test_name`), then the full list once at the end. If a command fails, fix the code.
