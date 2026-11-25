# ST09: Repository and ViewModel

Branch: `feature/streaming-st09-viewmodel` · PR into `develop` · PR title: `feat(frontend): stream answers in the assistant view model`

**Needs:** ST08 · **Effort:** 1–1.5 days · **Lane:** Android

## Goal

The assistant ViewModel shows the answer as it arrives, keeps every rule of today's chat (memory, budget, errors, unavailable state), and falls back to the old endpoint when the server has no stream.

Done when: every behaviour in *Tests to write first* passes; the existing `AssistantViewModelTest` cases pass unchanged against the streaming path (adapted only in how the fake repository answers).

## Files you own

`feature-assistant/.../repository/AssistantRepository.kt`, `AssistantViewModel.kt`, `ChatMemory.kt`, `core-model/.../Chat.kt` (`ChatMessage` only), `feature-assistant/src/androidUnitTest/.../AssistantViewModelTest.kt`, `feature-assistant/src/commonTest/.../AssistantRepositoryTest.kt`, `ChatMemoryTest.kt`, the module's DI file, this step's tracker row.

## Read first

`../contract.md` section 6, `AssistantViewModel.kt` (all of it), `AssistantRepository.kt`, `ChatMemory.kt` (`historyWindow` drops answers without a signature), `AssistantViewModelTest.kt`.

## Design (follow it)

- `ChatMessage` gains `isStreaming: Boolean = false` (KDoc: true while the answer is still arriving).
- `AssistantRepository.chatStream(message, conversationId, history, favouriteTeam): Flow<ChatStreamEvent>`. `DefaultAssistantRepository` remembers a `NotSupported` for the life of the repository and from then on, and for that same question, calls `chat()` and turns its `NetworkResult` into `Done` or `Failed`. So the ViewModel only ever sees the stream shape.
- `AssistantViewModel.send` collects `chatStream` in `viewModelScope`:
  - On the first `Delta`, add an assistant `ChatMessage(isStreaming = true)`; append later deltas to it. Push UI updates at most every 50 ms (inject the interval for tests; the last text before `Done` is always shown).
  - `Reset`: remove the streaming bubble's text (keep the typing indicator).
  - `Done`: replace the streaming bubble (or add one, if no delta came) with the final message built exactly as today (`answer`, sources, `retrievalConfidence`, `signature`), `isStreaming = false`; update `questionsLeft`.
  - `Failed`: the same branches as today's `NetworkResult.Error` (503 → `Unavailable`; 429 `REJECTED` → `questionsLeft = 0`; otherwise an error message with its `errorKind`), replacing any streaming bubble so no partial answer stays.
  - `isSending` stays true until a terminal event or failure; `newChat()` still does nothing while sending.
  - Cancelling (the ViewModel cleared) cancels the collection, which closes the connection.
- `historyWindow` must skip messages with `isStreaming = true` (belt and braces: they have no signature either).

## Tests to write first

In `AssistantViewModelTest` (fake repository returning a `MutableSharedFlow` or `flowOf`, `UnconfinedTestDispatcher`, Turbine on `state`):
- deltas build up one bubble; `isSending` true until `Done`;
- `Done` replaces the bubble with the signed answer and sets `questionsLeft`;
- `Reset` clears the text; the next deltas start again;
- `Done` with no delta adds the answer (router and refusal cases);
- `Failed` 503 → `Unavailable`; `Failed` 429 `REJECTED` → `questionsLeft == 0` and an error bubble; `Failed(OFFLINE)` mid-answer → the partial bubble becomes the error message;
- the next question's history excludes a failed or partial answer and includes the signed one;
- `newChat()` while streaming does nothing; idle reset still works;
- UI updates are throttled but the full text is shown before `Done`.
In `AssistantRepositoryTest`: `NotSupported` falls back to `chat()` for this and later questions; `chat()` success → `Done`, error → `Failed`.

## Verify by hand

Run the app on the Pixel 6 Pro emulator against the local backend (ST06 merged) and against a backend with `ASSISTANT_STREAMING=false`; both answer. Record a short note of what you saw.

## Docs to update

`frontend/feature-assistant/README.md` if it exists, this step's tracker row.

## Reviewer checklist

- [ ] Tests were written first (Red evidence in the PR).
- [ ] No partial or unsigned answer can reach `historyWindow`.
- [ ] Every old ViewModel test still passes.
- [ ] Throttle is injected; tests use virtual time, no real delays.

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b feature/streaming-st09-viewmodel`. If your environment assigns a branch name, use that instead and say so in the PR.
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
