# ST04: The stream gate

Branch: `feature/streaming-st04-stream-gate` · PR into `develop` · PR title: `feat(ai): hold back citations and ungrounded numbers while streaming`

**Needs:** ST01 · **Effort:** 1 day · **Lane:** Backend (can run beside ST02 and ST03)

## Goal

A small, pure class that decides which streamed text may go to the phone now, so streaming keeps today's guardrails: citations are never shown (ADR 029) and a follow-up never shows a number no tool returned (ADR 030).

Done when: for every way of splitting an answer into pieces, the gate releases exactly `strip_citations(answer)` (ignoring leading and trailing whitespace) when the answer is grounded, and reports "ungrounded" exactly when `ungrounded_numbers(answer, sources)` is non-empty, before releasing that number.

## Files you own

New `ai/assistant/services/stream_gate.py`, new `ai/tests/assistant/test_stream_gate.py`, this step's tracker row. `ai/assistant/grounding.py` and `ai/assistant/prompting/templates.py` only to make an existing private helper public (for example `_NAMES_WITH_DIGITS`); no behaviour change there.

## Read first

`ai/assistant/grounding.py`, `_CITATION` and `strip_citations` in `ai/assistant/prompting/templates.py`, `_recheck` in `ai/assistant/services/assistant_service.py`, ADR 029, ADR 030.

## Design (follow it)

```python
class StreamGate:
    def __init__(self, sources: Sequence[str] | None) -> None: ...
    def feed(self, text: str) -> GateStep: ...
    def finish(self) -> GateStep: ...

@dataclass(frozen=True)
class GateStep:
    release: str          # text safe to send now; may be ""
    ungrounded: list[str] # numbers that failed; non-empty means stop and reset
```

- `sources=None` means a first question: no number check (today's rule: the recheck runs only when there is history). A list means a follow-up: the user message and this turn's tool results, as `_recheck` builds them.
- Hold back: leading whitespace before the first visible character; any text from a `[` until the citation closes or it is clearly not a citation (the text after `[` stops matching `source:`); a number until the next character is neither a digit nor a `.` followed by a digit; trailing whitespace (released with the next visible text). "Ligue 1" is a name, not a number: reuse `_NAMES_WITH_DIGITS`.
- Decide with the existing functions (`numbers_in`, `matches`, `ungrounded_numbers`, the citation regex) so the gate and the non-streaming path can never disagree. Do not write a second number parser.
- Once `ungrounded` is non-empty, later `feed` calls release nothing.
- `finish()` releases what is held: an unclosed `[` is released as written, as `strip_citations` would leave it.

## Tests to write first

- Table tests: plain text; a citation split across three pieces; a citation at the very end; `[` that is not a citation (`[1]`, `[note]`); `47.` at a sentence end; `0.47`; `Ligue 1`; a grounded percentage (`47` against source `0.4712`); an ungrounded number on a follow-up returns it in `ungrounded` and releases none of it; the same number with `sources=None` is released.
- Property test, no new dependency: for 12 sample answers (with citations, decimals, percentages, Ligue 1, grounded and ungrounded numbers) and every split point, plus every split into single characters, check the released text and the verdict against `strip_citations` and `ungrounded_numbers`.

## Verify by hand

None: this class is pure, and the property test is the check.

## Docs to update

This step's tracker row.

## Reviewer checklist

- [ ] No second number or citation parser: the gate calls `grounding.py` and the template regex.
- [ ] Property test covers every split point of every sample.
- [ ] No ungrounded number is ever in `release` (look for a test that asserts it).

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b feature/streaming-st04-stream-gate`. If your environment assigns a branch name, use that instead and say so in the PR.
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
