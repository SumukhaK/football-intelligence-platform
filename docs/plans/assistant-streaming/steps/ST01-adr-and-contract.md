# ST01: ADR 037, API docs and telemetry contract 1.2.0

Branch: `docs/streaming-st01-adr-contract` · PR into `develop` · PR title: `docs(docs): decide how the assistant streams answers`

**Needs:** ST00 · **Effort:** 0.5 day · **Lane:** Contract (blocks both lanes)

## Goal

Turn the agreed contract into the project's official record, so both lanes can start.

Done when: ADR 037 is merged; `docs/api.md` documents `POST /v2/assistant/chat/stream` exactly as `../contract.md`; the telemetry contract is 1.2.0 with `ttft_ms` and `streamed` on `assistant.answer`; the spike's fallbacks are folded in.

## Files you own

`docs/adr/037-stream-assistant-answers.md` (new), `docs/adr/README.md`, `docs/api.md`, `docs/observability/telemetry-contract.md`, `docs/observability/telemetry-events.json`, `ai/shared/telemetry/json_formatter.py` (only `CONTRACT_VERSION`), `../contract.md` (only its header line, to point at `docs/api.md`), this step's tracker row.

## Read first

`../plan.md`, `../contract.md`, `docs/reports/assistant-streaming-spike.md` (ST00), ADRs 014, 018, 021, 024, 027, 029, 030, 034, 036.

## What to write

- **ADR 037.** Context: the latency numbers in `../plan.md`. Decision: a separate SSE endpoint under `/v2` only, the old endpoint unchanged, the stream gate (held-back citations and follow-up numbers), the four events, budget and signature once at `done`, disconnect behaviour and the `stopped` outcome (extends ADR 034's list), the `ASSISTANT_STREAMING` setting, Ktor 2.3.13 kept. Consequences: what a `reset` costs the user, the new outcome value, telemetry 1.2.0, ST00's fallbacks.
- **`docs/api.md`.** A new section after `POST /v2/assistant/chat` with sections 1 to 6 of `../contract.md`, and one example stream (copy `fixtures/answer.sse`).
- **Telemetry contract.** `assistant.answer` gains optional `ttft_ms` (int or null) and `streamed` (bool); version 1.2.0 in the header, the `contract_version` row and `CONTRACT_VERSION`; add `stopped` wherever question outcomes are listed. Update `telemetry-events.json` to match.

## Tests to write first

Change `ai/tests/shared/telemetry/test_json_formatter.py` to expect `contract_version == "1.2.0"` and add a test in `test_events.py` that `assistant.answer` in `telemetry-events.json` lists `ttft_ms` and `streamed`. Watch both fail, then bump the version and the events file.

## Verify by hand

Render `docs/api.md` and the ADR on GitHub; every link resolves.

## Docs to update

`docs/adr/README.md` index, `docs/README.md` if it lists ADRs, this step's tracker row.

## Reviewer checklist

- [ ] ADR has all five sections and names every ADR it extends (027, 029, 030, 034, 036).
- [ ] `docs/api.md` matches `../contract.md` word for word on event names, fields, headers and status codes.
- [ ] Telemetry contract, events JSON and `CONTRACT_VERSION` all say 1.2.0.

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b docs/streaming-st01-adr-contract`. If your environment assigns a branch name, use that instead and say so in the PR.
4. **Red.** Write the tests listed under *Tests to write first*. Run them and see each fail for the reason you expect (missing function, wrong value), not from a typo or an import error. Commit them first: `test(docs): ...`. Paste the failing summary line into the PR under **Red**.
5. **Green.** Write the least code that makes them pass. Then refactor with the tests green. Commit as `docs(docs): ...`.
6. Run every command under *Commands that must pass*. Paste each final summary line into the PR under **Commands**.
7. Do the *Verify by hand* check and write what you saw in the PR under **Manual check**.
8. Update the docs listed in the step, and this step's row and section in `../tracker.md`: status `Done (YYYY-MM-DD)`, ticked boxes, and the evidence links.
9. Open the PR into `develop` (never `main`) with the title given above and these sections: Summary, Red, Green, Commands, Manual check, Docs, New dependencies (say "None" or name each one and its ADR), Reviewer checklist (copy the step's list and tick it yourself).
10. Stop. Do not start the next step. Hand the PR to a reviewer with [`../review.md`](../review.md).

Never: skip, delete, weaken or mark as expected-failure an existing test to get green; change [`../contract.md`](../contract.md) or the fixtures (stop and raise it instead); touch files outside **Files you own** unless the step says so; leave a `TODO` without a linked issue; commit commented-out code; log the user's question or answer text.

## Rules for this step

- ADR format from `.claude/CLAUDE.md` section 17: Title, Status (Accepted), Context, Decision, Consequences. File `docs/adr/037-stream-assistant-answers.md`. Check `docs/adr/` on `develop` and open PRs for the next free number first; if 037 is taken, use the next one and replace "037" in every file of `docs/plans/assistant-streaming/`.
- Copy the contract, do not reword it: ST06 and ST08 test against the exact event names, fields and framing.
- Telemetry contract changes follow its own versioning rule: new optional fields are a minor bump.

## Commands that must pass (from `ai/`)

```bash
uv run pytest tests/shared -q
```

`telemetry-events.json` is loaded by tests (`test_events.py`); they must stay green after the version bump.
