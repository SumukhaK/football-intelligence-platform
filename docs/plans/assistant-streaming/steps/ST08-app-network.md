# ST08: Read the stream in the app's network layer

Branch: `feature/streaming-st08-network` · PR into `develop` · PR title: `feat(frontend): read streamed assistant answers in core-network`

**Needs:** ST01 · **Effort:** 1 day · **Lane:** Android (can run beside the whole backend lane)

## Goal

The app's network layer can call `POST /v2/assistant/chat/stream` and turn it into a `Flow` of typed events, following `../contract.md` exactly. No backend is needed: the tests read the shared fixtures.

Done when: `FootballApiService.chatStream(request)` emits the right events for every file in `../fixtures/`; errors before the stream map to the same `NetworkResult.Error` as `chat()`; a 404 gives `NotSupported`; cancelling the flow closes the connection; the stream is not logged by the `Logging` plugin.

## Files you own

`frontend/core-model/.../ChatStream.kt` (new), `frontend/core-network/.../SseParser.kt` (new), `FootballApiService.kt`, `CachingFootballApiService.kt`, `HttpClientFactory.kt`, `NetworkConfig.kt`, their tests in `core-network/src/commonTest` and `androidUnitTest`, this step's tracker row.

## Read first

`../contract.md`, `../fixtures/`, ST00's answer 3, `FootballApiService.kt` (`guarded`, `decode`, `toError`, `errorKindFor`), `HttpClientFactory.kt` (the `Logging` plugin is at `LogLevel.BODY`, which reads the whole body before handing it over), `NetworkConfig.kt`, `core-model/.../Chat.kt`.

## Design (follow it)

`core-model` `ChatStream.kt`:

```kotlin
sealed interface ChatStreamEvent {
    data class Delta(val text: String) : ChatStreamEvent
    data class Reset(val reason: ResetReason) : ChatStreamEvent
    data class Done(val response: ChatResponse) : ChatStreamEvent
    data class Failed(val error: NetworkResult.Error) : ChatStreamEvent
    data object NotSupported : ChatStreamEvent
}
enum class ResetReason { TOOL_CALL, GROUNDING, OTHER }
```

- `SseParser` (commonMain, pure): `feed(line: String): SseEvent?` and `end(): SseEvent?`. Handles `\r\n`, multiple `data:` lines (joined with `\n`), comment lines, `id:` and `retry:`; unknown event names are returned so the caller can skip them.
- `FootballApiService.chatStream(request: ChatRequest): Flow<ChatStreamEvent>` using `client.preparePost("$base/assistant/chat/stream") { ... header(Accept, "text/event-stream"); timeout { requestTimeoutMillis = config.chatStreamTimeoutMs; socketTimeoutMillis = config.timeoutMs } }.execute { ... bodyAsChannel().readUTF8Line() ... }` inside `flow { }`.
  - Non-2xx: 404 → `NotSupported`; otherwise `Failed(response.toError())`, the same error `chat()` gives.
  - `delta` → `Delta`, `reset` → `Reset` (unknown reason → `OTHER`), `done` → `Done` (decode `ChatResponse` with the client's JSON settings), `error` → `Failed(NetworkResult.Error(message = detail, code = 503, kind = ErrorKind.SERVER_BUSY))`, unknown event → skipped.
  - Stream ends without `done` or `error` → `Failed(... kind = ErrorKind.OFFLINE)`. Connection exceptions → `Failed(... OFFLINE)` as `guarded` does; `CancellationException` is rethrown.
  - Nothing is emitted after a terminal event.
- `NetworkConfig.chatStreamTimeoutMs: Long = 90_000L` (an answer with two tool rounds on a cold server can pass 30 s).
- `HttpClientFactory`: extend the `Logging` filter so `/assistant/chat/stream` is not logged (BODY logging would hold the stream back until it ends).
- `CachingFootballApiService.chatStream` delegates; chat is never cached.
- The stream request is never retried (`installGetRetry` only retries GET; keep it so).

## Tests to write first

- `core-network/src/commonTest/.../SseParserTest.kt`: framing cases, CRLF, multi-line data, comments, unknown events, `end()` with a half event.
- `core-network/src/androidUnitTest/.../ChatStreamFixturesTest.kt`: for each file in `../../docs/plans/assistant-streaming/fixtures/` (read with `java.io.File`, path relative to the module), serve it from Ktor `MockEngine` as the body and assert the emitted events: `answer.sse` → three `Delta`s and `Done` with signature and questions left; `tool_reset.sse` and `grounding_reset.sse` → the right `Reset` reasons; `refusal.sse` → `Done` with `model == "safety"` and null signature; `router.sse`; `error.sse` → `Failed` with `SERVER_BUSY`; `truncated.sse` → `Failed` with `OFFLINE`.
- Same file: 404 → `NotSupported`; 429 with the backend's JSON body → `Failed` with `REJECTED` and code 429 (same as `chat()`); 503 → `Failed` with `SERVER_BUSY`; an `IOException` from the engine → `Failed(OFFLINE)`; cancelling the collector stops reading.
- `HttpClientFactory` test (or `BearerAuthTest`-style): the stream URL is filtered out of logging; `/assistant/chat` still is not filtered.
- `CachingFootballApiServiceTest`: `chatStream` delegates and caches nothing.

## Verify by hand

With the backend from ST06 running if it exists yet (otherwise skip and say so): a throwaway unit test prints events with timestamps against `http://10.0.2.2:8000`. Not committed.

## Docs to update

`frontend/README.md` (network section) and this step's tracker row.

## Reviewer checklist

- [ ] Every fixture file has a test that reads the real file, not a copy.
- [ ] Pre-stream errors map exactly as `chat()` maps them (same `kind`, `code`, `message`).
- [ ] The stream URL is excluded from BODY logging.
- [ ] `CancellationException` rethrown; no emission after a terminal event.

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b feature/streaming-st08-network`. If your environment assigns a branch name, use that instead and say so in the PR.
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
