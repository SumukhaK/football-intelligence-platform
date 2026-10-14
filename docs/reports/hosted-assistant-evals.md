# Hosted assistant: model choice and evals

Run 10–11 October 2026 on the developer machine against Cloudflare Workers AI (hosting tracker step 3, ADR 025). Not yet run against staging.

## Index and retrieval cut-off

The knowledge base was re-indexed with `@cf/qwen/qwen3-embedding-0.6b` (1024 dimensions, 555 chunks) into its own folder, recorded in its `index.json`:

```sh
ASSISTANT_PROVIDER=workers_ai VECTOR_STORE_PATH=assistant/vector_store_workers_ai \
  uv run python -m assistant.pipeline --rebuild --min-relevance 0.77
```

`python -m evaluation.relevance_cutoff` scored the abstention eval's questions against it:

| Group | Best scores |
|---|---|
| In scope (10) | 0.797 to 0.863 |
| Out of scope (10) | 0.649 to 0.748 |

The groups separate cleanly, so the cut-off is **0.77**, midway between them. The local `nomic-embed-text` index keeps 0.81, where the two groups overlapped.

## Chat model

All three candidates support function calling and called the prediction tool in a live check. Each was then run through both evals with the hosted index.

| Model | Abstention | Grounding | Notes |
|---|---|---|---|
| `@cf/qwen/qwen3-30b-a3b-fp8` | 20/20 | 10/11 | Added an unsupported season number ("2026/27") |
| `@cf/zai-org/glm-4.7-flash` | not run | 10/11 | Same kind of unsupported number |
| `@cf/google/gemma-4-26b-a4b-it`, thinking on | 20/20 | 11/11 | p50 10 s, slowest 33 s, over the app's 30 s budget |
| **`@cf/google/gemma-4-26b-a4b-it`, thinking off** | **20/20** | **11/11** | **p50 3.0 s, slowest 14.2 s** |

The default is Gemma 4 26B with `WORKERS_AI_THINKING=false`: it passes both evals, and with its hidden reasoning off every answer fits the app's 30-second request budget.

## Cost

Over the 31 answers with thinking off, the mean list price was $0.000146 per answer, about 13 neurons. That is roughly 750 answers a day inside Workers AI's free 10,000 neurons, before embeddings, which are much cheaper.

## Conversational voice (15 October 2026)

The first use of staging on a phone showed stiff, report-like answers. The system prompt gained a "How you talk" section: answer first in plain words, then add one line of context from the data, keep to two to four sentences, and reply naturally to small talk without reciting rules. The grounding rules are unchanged. The app now hides the `[source: ...]` markers, which the server keeps for tracing.

Rerun with `@cf/google/gemma-4-26b-a4b-it`, thinking off: abstention 20/20, grounding 11/11, season 7/7. The grounding eval used to count "Ligue 1" as an invented number when an answer suggested other leagues; it now treats the league name as a name.

## Chat memory (15 October 2026)

The first run of the new conversation eval (`evaluation.assistant_conversation`, ADR 030) found two weaknesses, both now fixed:

- **Worked-out numbers in follow-ups.** Asked "and the draw?", the model often skipped the tool. It took 100% minus the two win chances from its earlier answer, and sometimes got it wrong (25.3% or 25.7% for a true 24.7%). Prompt wording did not stop it. The server now checks a follow-up's numbers against this turn's tool results and context, and asks the model once more when any number came from nowhere.
- **Wrong club names.** The model wrote "Ath Madrid" as "Athletic Madrid", and its next tool call failed on that name. The prompt now says to write team names exactly as the tools return them. A tool call that names no league now finds the league the two teams play in, instead of defaulting to the Premier League.

Run with `@cf/google/gemma-4-26b-a4b-it`, thinking off, the safety check on: abstention 20/20, grounding 11/11, season 7/7, conversation 8/8.

## Still to do

- Run both evals against staging (tracker step 3).
- Measure the first call after idle separately (tracker step 6).
