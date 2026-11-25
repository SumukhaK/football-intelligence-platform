# ST11: End-to-end check, staging and release notes

Branch: `docs/streaming-st11-release` · PR into `develop` · PR title: `docs(docs): record streaming end to end and on staging`

**Needs:** ST07, ST10 · **Effort:** 1 day · **Lane:** Integration (needs both lanes merged)

## Goal

Prove the app and backend work together, measure the real gain on staging, and update the docs that describe the assistant.

Done when: the end-to-end checklist below passes on the emulator against the local backend and against staging; the README release metrics show time to first word on staging; the roadmap entry is marked done; release notes are drafted.

## Files you own

`README.md` (release metrics and assistant sections), `CHANGELOG.md` (`[Unreleased]`), `docs/roadmap/future-improvements.md`, `docs/plans/assistant-streaming/plan.md` (status line), `docs/plans/assistant-streaming/tracker.md`, a new `docs/reports/assistant-streaming-e2e.md`, release-notes draft in `docs/releases/` for the next version.

## End-to-end checklist (local backend with Ollama, then staging)

1. First question with no tools: words appear before the answer finishes.
2. A prediction question (tool round): typing dots, then the answer; note any reset.
3. A follow-up ("and the away side?"): answer streams; history works on the next question.
4. A harmful test question from the safety eval: one-piece refusal, strike counted.
5. Budget used up (set a tiny per-user budget locally): 429 message, no stream.
6. Airplane mode mid-answer: the bubble becomes the offline error; the next question works.
7. Leave the screen mid-answer: the backend logs outcome `stopped` and charges the tokens.
8. Backend with `ASSISTANT_STREAMING=false`: the app still answers through the old endpoint.
9. Older app build (the last release APK) against the new backend: still answers.
10. TalkBack reads the answer once.

## Measure

From staging logs (`assistant.answer`), time to first word (`ttft_ms`) p50 and p95 against total answer time, split by path (`model`, `model_with_tools`, `router`). Compare with v2.6.3's 2,835 / 6,064 ms. Small samples: say how many.

## Verify by hand

The checklist above is the manual check; record each result in the report.

## Docs to update

All files in *Files you own*; mark the roadmap entry and `plan.md` "Done (date)"; every tracker row is `Done`.

## Reviewer checklist

- [ ] All ten end-to-end checks recorded with a result.
- [ ] Staging numbers come from logs, with sample sizes.
- [ ] Roadmap, plan, tracker, README and CHANGELOG all agree.

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b docs/streaming-st11-release`. If your environment assigns a branch name, use that instead and say so in the PR.
4. **Red.** Write the tests listed under *Tests to write first*. Run them and see each fail for the reason you expect (missing function, wrong value), not from a typo or an import error. Commit them first: `test(docs): ...`. Paste the failing summary line into the PR under **Red**.
5. **Green.** Write the least code that makes them pass. Then refactor with the tests green. Commit as `docs(docs): ...`.
6. Run every command under *Commands that must pass*. Paste each final summary line into the PR under **Commands**.
7. Do the *Verify by hand* check and write what you saw in the PR under **Manual check**.
8. Update the docs listed in the step, and this step's row and section in `../tracker.md`: status `Done (YYYY-MM-DD)`, ticked boxes, and the evidence links.
9. Open the PR into `develop` (never `main`) with the title given above and these sections: Summary, Red, Green, Commands, Manual check, Docs, New dependencies (say "None" or name each one and its ADR), Reviewer checklist (copy the step's list and tick it yourself).
10. Stop. Do not start the next step. Hand the PR to a reviewer with [`../review.md`](../review.md).

Never: skip, delete, weaken or mark as expected-failure an existing test to get green; change [`../contract.md`](../contract.md) or the fixtures (stop and raise it instead); touch files outside **Files you own** unless the step says so; leave a `TODO` without a linked issue; commit commented-out code; log the user's question or answer text.

## Rules for this step

- Follow the project's branch flow: everything is already on `develop`; this step proves it works together and writes it down. The release itself (PR `develop` → `main`, emulator smoke test, tag, debug APK and AAB assets) follows the usual release checklist and needs the owner's go-ahead.
- Deploying to staging follows `docs/plans/hosting-execution-tracker.md` and the staging runbook. Never change production.
- No secrets, tokens or personal data in reports or screenshots.

## Commands that must pass

Both lanes' full command lists on the merged `develop`, once:

```bash
cd ai && uv sync --extra dev && uv run ruff check . && uv run black --check . && uv run mypy . && uv run pytest --cov --cov-report=term-missing
cd ../frontend && ./gradlew spotlessCheck detekt testDebugUnitTest assembleDebug --no-daemon
```
