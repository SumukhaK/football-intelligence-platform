# Future Improvements

Ideas that are agreed in principle but not scheduled. Each one needs its own task, and an ADR where the rules in `.claude/CLAUDE.md` require one, before work starts.

## Stream assistant answers token by token

**Why:** the assistant waits for Workers AI (or Ollama locally) to finish the whole answer before it replies, so the first text a user sees is the complete answer. On staging that was p50 2,835 ms and p95 6,064 ms on v2.6.3, while the model's own time to first token is p50 486 ms and p95 1,280 ms when streamed (benchmark, 22 October 2026). Streaming would let the app show the answer as it is written, and would let us measure real time to first token on staging; today it can only be benchmarked separately (see [Release metrics](../../README.md#release-metrics)).

**What it involves:**
- Call the model with streaming on, in both the Workers AI and Ollama adapters.
- A streaming chat endpoint (for example server-sent events) next to `POST /v2/assistant/chat`, documented in `docs/api.md`. This changes the API contract, so it needs an ADR.
- The safety check, grounding and tool calls still run before any text is sent, and token budgets (ADR 036) are charged once the stream ends.
- A `ttft_ms` field on `assistant.answer`, which is a minor bump to the telemetry contract.
- The Android chat screen renders partial text, and still handles errors and the offline fallback.
