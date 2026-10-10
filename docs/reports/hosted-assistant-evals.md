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

## Still to do

- Run both evals against staging (tracker step 3).
- Measure the first call after idle separately (tracker step 6).
