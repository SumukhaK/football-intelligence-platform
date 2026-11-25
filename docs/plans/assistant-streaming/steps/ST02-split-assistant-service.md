# ST02: Split assistant_service.py before it grows

Branch: `refactor/streaming-st02-split-assistant-service` · PR into `develop` · PR title: `refactor(ai): move turn preparation and tool running out of assistant_service`

**Needs:** ST01 · **Effort:** 0.5 day · **Lane:** Backend

## Goal

`ai/assistant/services/assistant_service.py` is 405 lines, already over the 400-line limit, and streaming must reuse its steps. Move them into small modules with no change in behaviour, so ST05 can build the streaming path from the same parts.

Done when: `assistant_service.py` is under 300 lines; the parts below live in their own modules; every existing test passes unchanged (only import paths may change); no behaviour, log event or span changes.

## Files you own

`ai/assistant/services/assistant_service.py`, new `ai/assistant/services/turn.py` and `ai/assistant/services/tool_runner.py`, their tests, this step's tracker row.

## Read first

`ai/assistant/services/assistant_service.py`, `ai/tests/assistant/test_assistant_service.py`, `ai/tests/assistant/test_assistant_tracing.py`.

## Design (follow it)

- `turn.py`: the `_Turn` dataclass (rename to `TurnStats`, public, same fields plus nothing new yet), `_plus`, and a `TurnPreparer` that does what `chat()` does before the first model call: route (in its span), retrieve (in its span), build messages, run the router's calls. It returns a `PreparedTurn` (frozen dataclass: `messages`, `retrieved`, `route`, `routed_reply: str | None`, `stats`).
- `tool_runner.py`: `ToolRunner` with `run_calls(messages, calls, stats, content="")` and `run_tool(call)`, moved as they are, spans and `assistant.tool` events unchanged.
- `AssistantService` keeps `chat()`, `_answer`, `_recheck`, `_log_answer`, `_response` and composes the two new classes. Its constructor signature does not change.

## Tests to write first

- `ai/tests/assistant/test_turn.py`: a routed reply comes back as `routed_reply` with no retrieval; an unrouted question retrieves; a routed question with calls has the tool messages appended.
- `ai/tests/assistant/test_tool_runner.py`: a tool error marks the span and emits `assistant.tool` with `status=error`.
These pass once the code is moved. Their Red is "module not found"; that is the one step where that counts as the expected failure.

## Verify by hand

`git diff --stat` shows only moves and imports in `assistant_service.py`. Run one grounding eval question locally if Ollama is available and compare the answer to before.

## Docs to update

None beyond the tracker; this changes no behaviour.

## Reviewer checklist

- [ ] No test was edited except for import paths.
- [ ] Same spans, same events, same attribute names (check `test_assistant_tracing.py`).
- [ ] `assistant_service.py` under 300 lines; no new function over 40 lines.

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b refactor/streaming-st02-split-assistant-service`. If your environment assigns a branch name, use that instead and say so in the PR.
4. **Red.** Write the tests listed under *Tests to write first*. Run them and see each fail for the reason you expect (missing function, wrong value), not from a typo or an import error. Commit them first: `test(ai): ...`. Paste the failing summary line into the PR under **Red**.
5. **Green.** Write the least code that makes them pass. Then refactor with the tests green. Commit as `refactor(ai): ...`.
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
