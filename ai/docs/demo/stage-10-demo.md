# Stage 10 Demo — Football Intelligence Assistant

> Historical walkthrough of Stage 10 (v1.0.0 era). For the current system, use the root README Quick Start and docs/demo/README.md.

## Prerequisites

- Ollama installed and running: `ollama serve`
- Embedding model pulled: `ollama pull nomic-embed-text`
- Chat model pulled: `ollama pull llama3.2`
- Working directory: `ai/`

## Step 1 — Build the knowledge index

```sh
uv run python -m assistant.pipeline --rebuild
```

The last line of output reports the size of the index, for example:

```
Index built: 443 chunks in assistant/vector_store
```

The index now covers the model cards and reports under `models/`, the ADRs, the reports and the other top-level docs in `docs/`, plus the model's evaluation, metrics, SHAP summary and feature metadata JSON files. The current build has 443 chunks; your count depends on which docs and model runs you have locally. At Stage 10 it was 47 chunks.

## Step 2 — Query the index directly

```sh
uv run python -m assistant.pipeline
```

This loads the existing index and runs a sample query.

## Step 3 — Start the backend

```sh
uv run uvicorn backend.app.main:app --reload
```

Expected log output includes:

```
Assistant service loaded: 443 chunks in index.
```

## Step 4 — Check health

```sh
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "model_loaded": true,
  "explainability_available": true,
  "assistant_available": true,
  "fixture_features_available": true,
  "insights_available": true,
  "matches_through": "2026-09-20",
  "last_refresh_at": "2026-09-29T07:01:31+05:30",
  "last_refresh_error": null,
  "version": "2.0.0"
}
```

The dates depend on when your data was last refreshed.

## Step 5 — Chat with the assistant

```sh
curl -s -X POST http://localhost:8000/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the model accuracy and what features are most important?"}' \
  | python -m json.tool
```

Example response:

```json
{
  "answer": "The XGBoost model achieved 52.45% accuracy on the test set ...\n[source: model_card.md]",
  "sources": [
    {
      "source": "model_card.md",
      "excerpt": "| Accuracy | 0.5245 | ...",
      "relevance_score": 0.87
    }
  ],
  "confidence": 0.87,
  "model": "llama3.2",
  "retrieved_count": 3
}
```

## Step 6 — Verify 503 when index is missing

```sh
# Remove the index and restart
rm -rf assistant/vector_store
# Restart the server — it will log a warning and start without the assistant
curl -s http://localhost:8000/health | python -m json.tool
# "assistant_available": false

curl -s -X POST http://localhost:8000/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' 
# Returns 503
```

## Configuration

Override defaults with environment variables:

```sh
OLLAMA_CHAT_MODEL=llama3.1 \
OLLAMA_EMBED_MODEL=nomic-embed-text \
ASSISTANT_TOP_K=3 \
uv run uvicorn backend.app.main:app
```
