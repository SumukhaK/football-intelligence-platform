# ST05: Streaming answers in the assistant

Branch: `feature/streaming-st05-assistant-stream` · PR into `develop` · PR title: `feat(ai): stream assistant answers after the tool rounds`

**Needs:** ST02, ST03, ST04 · **Effort:** 1–1.5 days · **Lane:** Backend

## Goal

The assistant can answer a question as a sequence of events (`Delta`, `Reset`, `Final`) that follows the same steps as `AssistantService.chat()`: router, retrieval and relevance cut-off, tool rounds, grounding retry. Text passes through the stream gate.

Done when: `StreamingAnswerer.answer(question, history)` yields events whose joined text equals `chat()`'s answer for the same fakes; every guardrail in *Invariants* below has a test; `assistant.answer` carries `ttft_ms` and `streamed`.

## Files you own

New `ai/assistant/services/streaming_answerer.py` and `ai/assistant/services/answer_events.py`, `ai/assistant/services/turn.py` (only to share code), `ai/assistant/pipeline.py` (to build it next to `get_service()`), their tests, this step's tracker row. Do not add to `assistant_service.py` beyond moving `_log_answer` into a shared place if both paths need it.

## Read first

`ai/assistant/services/assistant_service.py`, `turn.py` and `tool_runner.py` (ST02), `ai/assistant/generation/streaming.py` (ST03), `ai/assistant/services/stream_gate.py` (ST04), `../contract.md` sections 4 and 5.

## Design (follow it)

`answer_events.py`: frozen dataclasses `Delta(text: str)`, `Reset(reason: Literal["tool_call", "grounding"])`, `Final(response: AssistantResponse)`; `AnswerEvent = Delta | Reset | Final`.

`StreamingAnswerer` is built from the same parts as `AssistantService` (`TurnPreparer`, `ToolRunner`, the generator, the model name, a clock). `answer()` is a generator:

1. Validate the question and the index exactly as `chat()` does (same exceptions).
2. `TurnPreparer` runs route, retrieval and router calls. A routed reply yields `Delta(reply)` then `Final`.
3. If the generator is not a `StreamingGenerator` or no tools are configured, call it the non-streaming way and yield one `Delta` and `Final` (keeps fakes and odd providers working).
4. Tool loop, up to `_MAX_TOOL_ROUNDS` like `_answer`. For each model call, consume `chat_stream`: feed `TextPiece`s into a `StreamGate` and yield its releases as `Delta`; on a `ToolCallsPiece`, if any `Delta` was yielded since the last reset, yield `Reset("tool_call")`; then run the calls with `ToolRunner` (the text so far goes in the assistant message as today) and start the next round with a new gate. Add each `UsagePiece` to the stats. The round-limit fallback is the same as `_answer`, including its `fallback` event.
5. Grounding: the gate gets `sources` only when history is non-empty (same rule as `_recheck`). If it reports `ungrounded`, close the model stream at once, emit the same `guardrail.event` (`kind=grounding`, `outcome=retried`), yield `Reset("grounding")`, append the same two messages as `_recheck`, and stream one more answer with `sources=None` (today's recheck also checks only once).
6. Build the `AssistantResponse` with `_response()`'s rules (confidence, sources, `tokens_used`), yield `Final`, and log `assistant.answer` as `_log_answer` does plus `ttft_ms` (clock at the first `Delta` minus start, or None) and `streamed=True`. The non-streaming path logs `streamed=False` and `ttft_ms=None`.
7. A `finally` closes the current model stream, so closing the answerer early stops the model.

`AssistantPipeline.get_streaming_answerer()` builds it from the loaded index like `get_service()`.

## Invariants (each needs a test)

- No `Delta` before routing, retrieval and router calls finish (fake generator records when it is first called; a fake tool records order).
- A `ToolCallsPiece` after text gives `Reset("tool_call")` before the tool runs; text before a tool call with no `Delta` yet gives no `Reset`.
- On a follow-up, an ungrounded number never appears in any `Delta`; `Reset("grounding")` follows and the retry streams.
- Joined `Delta` text since the last `Reset` equals `Final.response.answer` after `strip_citations` and `.strip()`, for: plain answer, one tool round, two tool rounds, round limit, grounding retry, routed reply.
- Usage from every round is summed into `tokens_used`.
- Closing the generator after the first `Delta` closes the fake model stream and logs nothing as answered.
- Same `assistant.tool`, `fallback`, `guardrail.event` and span names as the non-streaming path.

## Tests to write first

`ai/tests/assistant/test_streaming_answerer.py` with a scripted fake `StreamingGenerator` (a list of piece lists, one per round) and fake tools; one test per invariant above; plus `ai/tests/assistant/test_assistant_tracing.py` cases for the streaming spans.

## Verify by hand

With Ollama: a short script prints each event with a timestamp for one grounding-eval question and one follow-up. Paste the output.

## Docs to update

`ai/assistant/README.md` (module list), this step's tracker row.

## Reviewer checklist

- [ ] Every invariant above has a named test.
- [ ] Same events and spans as the non-streaming path, plus `ttft_ms` and `streamed`.
- [ ] `finally` closes the model stream; a test proves it.
- [ ] No file over 400 lines; `assistant_service.py` did not grow.

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b feature/streaming-st05-assistant-stream`. If your environment assigns a branch name, use that instead and say so in the PR.
4. **Red.** Write the tests listed under *Tests to write first*. Run them and see each fail for the reason you expect (missing function, wrong value), not from a typo or an import error. Commit them first: `test(ai): ...`. Paste the failing summary line into the PR under **Red**.
5. **Green.** Write the least code that makes them pass. Then refactor with the tests green. Commit as `feat(ai): ...`.
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
