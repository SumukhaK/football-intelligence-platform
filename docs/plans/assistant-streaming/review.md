# Reviewing a streaming step

Paste this file into a fresh thread with: "Review PR #n. Its step file is `docs/plans/assistant-streaming/steps/STnn-....md`." You need nothing else from earlier conversations.

## 1. Read

1. `.claude/CLAUDE.md` (sections 10, 12, 14, 16).
2. The step file named above, in full.
3. [contract.md](contract.md) and [tracker.md](tracker.md).
4. The PR: description, every commit, and the full diff.

## 2. Check the work against the step

- [ ] **Needs:** every step it needs was `Done` before this PR branched.
- [ ] **Scope:** every changed file is in the step's *Files you own*. Anything else is either removed or explained and agreed.
- [ ] **Done when:** each sentence of the step's *Done when* is true, and you can point to the test or evidence that shows it.
- [ ] **Tests first:** the PR has a Red run that failed for the right reason, and the test commit comes before the code commit (or the PR explains why not).
- [ ] **Every listed test exists:** go down the step's *Tests to write first* and find each one by name. A missing one is a finding.
- [ ] **Design followed:** class names, signatures, event names and file names match the step. A deviation needs a reason in the PR.
- [ ] **Step checklist:** every box in the step's *Reviewer checklist* is truly met, not just ticked.
- [ ] **Docs and tracker:** the docs the step lists are updated, and its tracker row and section show `Done` with evidence links.

## 3. Run it yourself

Check out the PR branch in a clean clone and run the step's *Commands that must pass*. Then run the cross-lane contract tests, whichever exist yet:

```bash
cd ai && uv run pytest tests/backend/test_assistant_stream_endpoint.py tests/evaluation/test_stream_client.py -q
cd frontend && ./gradlew :core-network:testDebugUnitTest --tests '*ChatStreamFixturesTest*' --no-daemon
```

Do the step's *Verify by hand* check if you can run it; otherwise say so.

## 4. Invariants (none may break, in any step)

| # | Invariant |
|---|---|
| I1 | No answer text leaves the server before the history check, safety check, budget check, season router, and retrieval with its relevance cut-off have finished. |
| I2 | Text from a reply that turns into a tool call is followed by a `reset` before the tool runs. |
| I3 | On a follow-up, no number that no tool returned this turn appears in any `delta`. |
| I4 | No `[source: ...]` citation appears in any `delta` or in `done.answer`. |
| I5 | The `delta` texts since the last `reset`, joined, equal `done.answer` apart from leading and trailing whitespace. |
| I6 | Per question: budget charged once, signature only on `done`, question stored once. |
| I7 | A client disconnect stops the model call, runs the `finally`, charges what was used and stores `stopped`. |
| I8 | `POST /v2/assistant/chat` and everything under `/v1` behave exactly as before. The stream route exists only under `/v2`, with the consent guard. |
| I9 | No question or answer text in any log line, span or metric. |
| I10 | The app never sends a partial or unsigned answer back as history, and keeps Send and New chat disabled until the stream ends. |
| I11 | Every event name, field, header and status code matches [contract.md](contract.md) and the [fixtures](fixtures/). |
| I12 | Old app builds still work against the new backend; the new app still works against a backend with streaming off. |

## 5. Code quality

- [ ] CLAUDE.md limits: files under 400 lines, functions under 40, docstrings or KDoc, types on every signature.
- [ ] No placeholder code, no commented-out code, no `TODO` without an issue, no new dependency without an ADR.
- [ ] Errors to clients use `{"error": ..., "detail": ...}`; provider error text never reaches the client.
- [ ] Tests are deterministic: injected clocks, sleeps and throttles; no network; no real model in unit tests.
- [ ] Kotlin: strings in `composeResources`, content descriptions, a `@Preview` per Composable, `CancellationException` rethrown.

## 6. Finish

- Post one review on the PR listing each finding with the file and line, ending with the footer the project uses for generated comments.
- Fix small findings on the branch yourself (tests first), push, and re-run the commands. Ask the author's thread to fix larger ones.
- When everything above passes and CI is green (or a red check is shown to be red on `develop` too and named in the PR), merge into `develop`, and make sure the tracker row says `Done (date, PR #n)`.
- Never merge into `main`.
