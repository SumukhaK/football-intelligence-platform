# ST03: Streaming in the Ollama and Workers AI adapters

Branch: `feature/streaming-st03-adapters` · PR into `develop` · PR title: `feat(ai): stream chat replies from ollama and workers ai`

**Needs:** ST01 · **Effort:** 1–1.5 days · **Lane:** Backend (can run beside ST02 and ST04)

## Goal

Both chat adapters can hand back a reply piece by piece, including tool calls and token usage, so the assistant can stream.

Done when: `OllamaGenerator` and `WorkersAIGenerator` implement `StreamingGenerator.chat_stream`; the existing `chat()` and `generate()` are unchanged; retries happen only before the first piece; closing the iterator early closes the upstream connection.

## Files you own

New `ai/assistant/generation/streaming.py`, `ai/assistant/generation/generator.py`, `ai/assistant/workers_ai.py` (split into `workers_ai_stream.py` if it would pass 400 lines), their tests, this step's tracker row.

## Read first

`docs/reports/assistant-streaming-spike.md` answers 1 and 2, `ai/assistant/generation/generator.py`, `ai/assistant/workers_ai.py`, `ai/shared/telemetry/retry.py`, `ai/tests/assistant/test_generator.py`, `ai/tests/assistant/test_workers_ai.py`.

## Design (follow it)

`streaming.py`:

```python
@dataclass(frozen=True)
class TextPiece:        # some answer text, possibly whitespace
    text: str
@dataclass(frozen=True)
class ToolCallsPiece:   # the complete tool calls of this reply
    calls: list[ToolCall]
@dataclass(frozen=True)
class UsagePiece:       # last piece; None fields mean "not reported"
    prompt_tokens: int | None
    completion_tokens: int | None
    cost_usd: float | None
StreamPiece = TextPiece | ToolCallsPiece | UsagePiece

@runtime_checkable
class StreamingGenerator(Protocol):
    def chat_stream(self, messages, tools) -> Iterator[StreamPiece]: ...
```

Rules for every adapter: yield `TextPiece`s in order; yield at most one `ToolCallsPiece`, holding complete, parsed calls (join Workers AI's argument fragments by `index` before `json.loads`; bad JSON gives `{}` as `_tool_call` does today); yield exactly one `UsagePiece` last. The iterator is a generator whose `finally` closes the HTTP stream or Ollama iterator.

- **Ollama:** `client.chat(..., stream=True)`; text from `chunk.message.content`, tool calls from `chunk.message.tool_calls`, usage from the chunk with `done=True`. Errors raise `OllamaGenerationError` as today, also mid-stream.
- **Workers AI:** add a `stream(path, body)` method on `WorkersAIClient` built on an injected `Stream` callable (default `httpx.stream`), mirroring how `post` is injected today. Send `"stream": true` and `"stream_options": {"include_usage": true}`. Parse `data:` lines; stop at `data: [DONE]`. Apply `RETRY_POLICY` to opening the stream and reading up to the first piece only; after a piece was yielded, any error raises `WorkersAIError` without retry. Cost from `usage.neurons` as in `parse_turn`.
- Emit `dependency.call` per attempt as the non-streaming path does.

## Tests to write first

- `ai/tests/assistant/test_streaming_ollama.py` (fake `ollama.Client` via monkeypatch): text pieces in order; tool calls in a chunk become one `ToolCallsPiece`; usage last; an exception mid-stream raises `OllamaGenerationError`; `close()` on the iterator closes the fake stream.
- `ai/tests/assistant/test_streaming_workers_ai.py` (fake `Stream` returning scripted SSE lines): text; tool-call fragments over three events joined into one call with parsed arguments; bad argument JSON gives `{}`; `usage` with `neurons` gives `cost_usd`; no usage gives `UsagePiece(None, None, None)`; a 503 before the first piece is retried once (inject `sleep`); a connection error after the first piece raises without retry; `close()` closes the response.
- Joining all `TextPiece`s equals what `chat()` returns for the same scripted reply (one test per adapter).

## Verify by hand

With Ollama running: a 10-line script in a Python shell calls `chat_stream` for one fixture question and prints each piece with a timestamp. Paste the output (no secrets).

## Docs to update

`ai/assistant/README.md` (if it lists modules), this step's tracker row.

## Reviewer checklist

- [ ] Retry never happens after the first piece.
- [ ] Early `close()` closes the upstream stream in both adapters (tests prove it).
- [ ] `chat()` and `generate()` untouched; their tests unchanged.
- [ ] No token, account ID or URL in error messages returned upward.

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b feature/streaming-st03-adapters`. If your environment assigns a branch name, use that instead and say so in the PR.
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
