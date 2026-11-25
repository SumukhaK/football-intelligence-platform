# ST07: Evals through the streaming endpoint

Branch: `feature/streaming-st07-evals` · PR into `develop` · PR title: `ai(ai): run the assistant evals through the streaming endpoint`

**Needs:** ST06 · **Effort:** 0.5–1 day · **Lane:** Backend

## Goal

Prove streamed answers are as good as non-streamed ones: the grounding, season, abstention and conversation evals run through the stream endpoint with the same pass rates.

Done when: each assistant eval CLI takes `--stream`; a run on the local model is recorded in `docs/reports/assistant-streaming-evals.md` with both modes side by side; no eval scores lower when streamed.

## Files you own

`ai/evaluation/assistant_grounding.py`, `assistant_season.py`, `assistant_abstention.py`, `assistant_conversation.py`, a new shared helper `ai/evaluation/stream_client.py`, their tests, `docs/reports/assistant-streaming-evals.md`, `ai/evaluation/README.md`, this step's tracker row.

## Design (follow it)

`stream_client.py`: `ask_streamed(client, body) -> StreamedAnswer` posts to `/v2/assistant/chat/stream` with `TestClient`, parses the events with a small parser (the same framing rules as contract section 3), and returns the `done` response plus checks: joined deltas since the last reset equal `done.answer` (whitespace-trimmed), a `done` or `error` arrived, the number of resets and their reasons. Each eval's `_ask` uses it when `--stream` is set and fails the case if a check fails.

## Tests to write first

`ai/tests/evaluation/test_stream_client.py`: parses every file in `docs/plans/assistant-streaming/fixtures/`; flags a mismatch between joined deltas and `done.answer`; flags `truncated.sse` as missing a terminal event.

## Verify by hand

Run each eval twice, plain and `--stream`, on `qwen2.5:7b-instruct`, and on the hosted model if the Workers AI token is set locally. Record pass counts, resets seen, and time to first `delta` (median of the cases).

## Docs to update

The new report, `ai/evaluation/README.md`, `docs/README.md` reports list, this step's tracker row.

## Reviewer checklist

- [ ] Same pass counts with and without `--stream` (or a written reason for each difference).
- [ ] Every streamed case checked joined deltas against `done.answer`.

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b feature/streaming-st07-evals`. If your environment assigns a branch name, use that instead and say so in the PR.
4. **Red.** Write the tests listed under *Tests to write first*. Run them and see each fail for the reason you expect (missing function, wrong value), not from a typo or an import error. Commit them first: `test(ai): ...`. Paste the failing summary line into the PR under **Red**.
5. **Green.** Write the least code that makes them pass. Then refactor with the tests green. Commit as `ai(ai): ...`.
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
