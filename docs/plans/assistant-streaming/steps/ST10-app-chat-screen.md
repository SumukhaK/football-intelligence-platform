# ST10: Chat screen shows the answer as it arrives

Branch: `feature/streaming-st10-chat-screen` · PR into `develop` · PR title: `feat(frontend): show assistant answers as they stream`

**Needs:** ST09 · **Effort:** 1–1.5 days · **Lane:** Android

## Goal

The chat screen renders the growing answer smoothly and accessibly.

Done when: the typing dots show only until the first word (and again after a reset); the bubble grows and the list follows it; TalkBack announces the answer once, when it is done; previews and strings are in place.

## Files you own

`feature-assistant/.../AssistantScreen.kt` (split into `AssistantMessageList.kt` if it would pass 400 lines; it is 316 today), `AnswerFormatting.kt`, `feature-assistant/src/androidMain/.../AssistantPreviews.kt`, `feature-assistant/src/commonMain/composeResources/values/strings.xml`, Compose UI tests if the module has them, this step's tracker row.

## Read first

`AssistantScreen.kt` (the `isSending` indicator and the `LaunchedEffect(messages.size)` scroll), `AnswerFormatting.kt` (`formatAnswer` shows an unmatched `**` as written), `AssistantPreviews.kt`, ADR 010.

## Design (follow it)

- Typing indicator: show while `isSending` and the last message is not a streaming assistant message with text.
- Scroll: key the scroll effect on both the message count and the last message's text length, and only follow when the user is already at the bottom (do not pull them down while they read older messages).
- Bold while streaming: `formatAnswer` already leaves an unmatched `**` as written; for a streaming message, hide a trailing unmatched `**` so it does not flash. Unit-test this in `AnswerFormattingTest`.
- Accessibility: the streaming bubble has a content description from `strings.xml` (for example "Assistant is answering"); set `liveRegion = Polite` only on the finished message, so TalkBack reads it once.
- New strings only in `composeResources/values/strings.xml`.
- Previews: a bubble mid-answer, a bubble after a reset (typing dots), and the finished answer.

## Tests to write first

- `AnswerFormattingTest`: a streaming message ending in an unmatched `**` hides it; a finished one shows it as today.
- A Compose UI test (or, if the module has none, a test of the state-to-UI helper you extract) for: typing dots before the first delta, no dots while text is arriving, dots after a reset.

## Verify by hand

On the Pixel 6 Pro emulator (never the Pixel 7 API 35 image, its networking is broken) against the local backend: ask a tool question and a follow-up; watch for reset flicker; turn TalkBack on and check it reads the answer once. Record a short screen capture for the PR (not in Firefox; use the emulator's recorder).

## Docs to update

This step's tracker row; screenshots for the release notes go to ST11.

## Reviewer checklist

- [ ] No hardcoded user-facing text; content descriptions present.
- [ ] Every new Composable has a `@Preview`.
- [ ] The list does not jump when the user has scrolled up.
- [ ] Screen recording attached to the PR.

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b feature/streaming-st10-chat-screen`. If your environment assigns a branch name, use that instead and say so in the PR.
4. **Red.** Write the tests listed under *Tests to write first*. Run them and see each fail for the reason you expect (missing function, wrong value), not from a typo or an import error. Commit them first: `test(frontend): ...`. Paste the failing summary line into the PR under **Red**.
5. **Green.** Write the least code that makes them pass. Then refactor with the tests green. Commit as `feat(frontend): ...`.
6. Run every command under *Commands that must pass*. Paste each final summary line into the PR under **Commands**.
7. Do the *Verify by hand* check and write what you saw in the PR under **Manual check**.
8. Update the docs listed in the step, and this step's row and section in `../tracker.md`: status `Done (YYYY-MM-DD)`, ticked boxes, and the evidence links.
9. Open the PR into `develop` (never `main`) with the title given above and these sections: Summary, Red, Green, Commands, Manual check, Docs, New dependencies (say "None" or name each one and its ADR), Reviewer checklist (copy the step's list and tick it yourself).
10. Stop. Do not start the next step. Hand the PR to a reviewer with [`../review.md`](../review.md).

Never: skip, delete, weaken or mark as expected-failure an existing test to get green; change [`../contract.md`](../contract.md) or the fixtures (stop and raise it instead); touch files outside **Files you own** unless the step says so; leave a `TODO` without a linked issue; commit commented-out code; log the user's question or answer text.

## Kotlin rules (from `.claude/CLAUDE.md`; apply to every file you write)

- Work in `frontend/`. MVVM: one ViewModel per screen, UI state in `StateFlow`, Composables stateless (state in, events out).
- Network calls go through a repository interface; the ViewModel never calls the API.
- TDD is required for ViewModels and repositories: the test is written and seen failing before the code.
- Prefer `val`; immutable data classes. No nullable type without a reason in its KDoc. Sealed types over nullable returns. `when` is exhaustive.
- Coroutines scoped to the ViewModel; no `GlobalScope`. Cancellation (`CancellationException`) is always rethrown.
- No hardcoded user-facing text: strings go in the module's `composeResources/values/strings.xml` (ADR 010). Content descriptions on every interactive element.
- Every Composable has a `@Preview` in the module's `androidMain` previews file.
- No file over 400 lines, no function over 40 lines. KDoc on every public class and function.
- Tests use JUnit 5, MockK, Turbine and `kotlinx-coroutines-test` (already in the catalogue). No new dependency without an ADR; this feature needs none (Ktor 2.3.13 reads the stream with `bodyAsChannel()`).
- Conventional Commits with scope `frontend`.

## Commands that must pass (from `frontend/`)

```bash
./gradlew spotlessCheck detekt --no-daemon
./gradlew testDebugUnitTest --no-daemon
./gradlew assembleDebug --no-daemon
```

While fixing a failure, re-run only the failing module's tests (for example `./gradlew :feature-assistant:testDebugUnitTest --tests '*AssistantViewModelTest*'`), then the full list once at the end.
