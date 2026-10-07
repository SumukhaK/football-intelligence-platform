# ADR 018 — Assistant Tool Calling over the API's Own Services

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The assistant answered only from documents retrieved from its index: model
cards, evaluation reports, SHAP summaries and ADRs. None of those hold a
prediction for a specific match, so "What does the model predict for Arsenal
vs Leeds?" could only be refused. Asked for ten real fixtures across the five
leagues, the assistant refused all ten.

The numbers users want are already served by POST /v2/predict, POST
/v2/explain and GET /v2/fixtures. The project rules forbid fine-tuning
(`.claude/CLAUDE.md`, section 5), so the fix has to come from prompts, tools
and data.

## Decision

1. **Tools.** The assistant offers the chat model three function-calling
   tools: `predict_match`, `explain_match` and `upcoming_fixtures`. Ollama's
   chat API carries the tool schemas and the model's calls.
2. **Same code as the endpoints.** Each tool runs the service its endpoint
   uses (`PredictionService`, `ExplanationService`, `FixturesService`, with
   features from `FixtureFeatureService`), in-process, not over HTTP. The
   assistant therefore quotes exactly what /v2 returns, from the latest model.
   Services are read from `app.state` on each call because the daily refresh
   (ADR 013) replaces them.
3. **Layering.** The assistant package defines `Tool` and the tool-calling
   loop and knows nothing about FastAPI. The backend builds the tools in
   `backend/app/services/assistant_tools.py` and injects them at startup.
4. **Errors.** An expected failure (unknown team or league, model not loaded,
   bad arguments) goes back to the model as `{"error": ...}` so it can tell the
   user. Any other exception propagates and the chat endpoint answers 503.
5. **Bounded loop.** The model gets at most three rounds of tool calls, then is
   asked for its answer without tools.
6. **Prompt.** The system prompt tells the model to call a tool for match
   predictions, explanations and fixtures, to quote the tool's numbers (a
   probability may be written as a percentage) and never to compute its own,
   and to cite tool results as `[source: tool <name>]`.
7. **Evaluation.** `ai/evaluation/assistant_grounding.py` asks for the
   prediction of upcoming fixtures in every league, calls /v2/predict and
   /v2/explain for the same matches, and checks that each answer quotes the
   predicted outcome's probability and contains no number those responses or
   the question do not account for. It also asks about a team that does not
   exist and checks no numbers are invented.

## Consequences

- On 7 October 2026 with `qwen2.5:7b-instruct`, the evaluation passed 11 of 11
  cases with tools (10 fixtures plus the unknown team) against 1 of 11 without
  them, where every fixture question was refused.
- The configured default model, `llama3.2`, supports tool calling. A model
  that does not will error on the first chat, so `OLLAMA_CHAT_MODEL` must name
  a tool-capable model.
- A prediction answer can take two or three model calls instead of one.
- The chat response's `confidence` is still the retrieval score, so an answer
  grounded in a tool result can show low confidence.
- The evaluation needs Ollama and the trained model, so it runs locally, not
  in CI. Its scoring functions are unit-tested in CI.
