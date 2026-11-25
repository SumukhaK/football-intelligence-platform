# ST00: Spike: can every link stream?

Branch: `docs/streaming-st00-spike` · PR into `develop` · PR title: `docs(docs): record the assistant streaming spike`

**Needs:** nothing · **Effort:** 0.5 day · **Lane:** Spike (run on the owner's PC: it needs Ollama, the Workers AI token and the Android SDK)

## Goal

Find out, before anyone writes product code, whether each link in the chain can stream. Every later step assumes these answers.

Done when: `docs/reports/assistant-streaming-spike.md` answers the five questions below with evidence, and names a fallback for every "no".

## Files you own

`docs/reports/assistant-streaming-spike.md` (new), this step's row in `../tracker.md`.

## Questions to answer

1. **Ollama, local model** (`qwen2.5:7b-instruct`, the `ollama_chat_model` default): with `client.chat(..., tools=[...], stream=True)`, do tool calls arrive in a chunk? Does the model ever write text before its tool call in the same turn? Do the last chunk's `prompt_eval_count` and `eval_count` arrive? Use the three tool schemas from `ai/backend/app/services/assistant_tools.py` and five questions from `ai/evaluation/assistant_grounding.py`.
2. **Workers AI, hosted model** (`workers_ai_chat_model`, `@cf/google/gemma-4-26b-a4b-it`, thinking off): with `"stream": true` on `chat/completions` and tools offered, do tool calls stream as OpenAI-style `delta.tool_calls` pieces? Is `usage` (with `neurons`) in the last event when you send `"stream_options": {"include_usage": true}`? Time to first text piece for five questions.
3. **Ktor on Android** (2.3.13, `ktor-client-android` engine): in a throwaway JVM unit test in `core-network`, does `client.preparePost(url).execute { it.bodyAsChannel().readUTF8Line() }` hand over each line as it arrives from a local test server that writes one event every 500 ms? Then repeat with the app's `Logging` plugin at `LogLevel.BODY`: does it hold the body back until the end? (Expected: yes, so ST08 must filter the stream URL out of logging.)
4. **Cloud Run**: confirm from Google's documentation that HTTP/1.1 streamed responses pass through without buffering, and the request timeout setting staging uses (`infrastructure/` or the staging runbook). Link the page.
5. **Disconnect**: with FastAPI's `StreamingResponse` over a sync generator, does the generator's `finally` run when the client disconnects mid-stream? Test with a throwaway app and `curl --max-time 1`.

## Verify by hand

Each answer quotes the command or test that produced it and its output (trimmed).

## Docs to update

- The report, linked from `docs/README.md` under Reports.
- `../tracker.md`: this row, and in the Decisions log any fallback chosen. If a fallback needs a new dependency (for example the OkHttp engine) or changes `../contract.md`, say so plainly: ST01 must then cover it in ADR 037 before any lane starts.

## Reviewer checklist

- [ ] All five questions answered with evidence, not opinion.
- [ ] Every "no" has a named fallback and its effect on later steps.
- [ ] No secret, token, account ID or personal data in the report.

## How to work (every step)

1. Read `.claude/CLAUDE.md`, then this file, then [`../contract.md`](../contract.md) and [`../tracker.md`](../tracker.md). If anything here disagrees with CLAUDE.md, CLAUDE.md wins: say so in the PR description.
2. Check the tracker: every step under **Needs** must be `Done`. If one is not, stop and say which.
3. Branch from the latest `develop`: `git checkout develop && git pull && git checkout -b docs/streaming-st00-spike`. If your environment assigns a branch name, use that instead and say so in the PR.
4. **Red.** Write the tests listed under *Tests to write first*. Run them and see each fail for the reason you expect (missing function, wrong value), not from a typo or an import error. Commit them first: `test(docs): ...`. Paste the failing summary line into the PR under **Red**.
5. **Green.** Write the least code that makes them pass. Then refactor with the tests green. Commit as `docs(docs): ...`.
6. Run every command under *Commands that must pass*. Paste each final summary line into the PR under **Commands**.
7. Do the *Verify by hand* check and write what you saw in the PR under **Manual check**.
8. Update the docs listed in the step, and this step's row and section in `../tracker.md`: status `Done (YYYY-MM-DD)`, ticked boxes, and the evidence links.
9. Open the PR into `develop` (never `main`) with the title given above and these sections: Summary, Red, Green, Commands, Manual check, Docs, New dependencies (say "None" or name each one and its ADR), Reviewer checklist (copy the step's list and tick it yourself).
10. Stop. Do not start the next step. Hand the PR to a reviewer with [`../review.md`](../review.md).

Never: skip, delete, weaken or mark as expected-failure an existing test to get green; change [`../contract.md`](../contract.md) or the fixtures (stop and raise it instead); touch files outside **Files you own** unless the step says so; leave a `TODO` without a linked issue; commit commented-out code; log the user's question or answer text.

## Rules for this step

- This step answers questions; it ships no product code. Throwaway scripts stay out of Git; paste their source into the report's appendix so anyone can rerun them.
- Never paste the Workers AI token, account ID or any other secret into the report, a commit or a log. Read them from `ai/.env` as the app does.
- Keep the report under 200 lines, in simple English, with the raw numbers.

## Commands that must pass

None beyond the repository checks CI runs on Markdown.
