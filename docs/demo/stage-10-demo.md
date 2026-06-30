# Stage 10 Demo — Football Intelligence Assistant

## Prerequisites

- Ollama installed and running: `ollama serve`
- Embedding model pulled: `ollama pull nomic-embed-text`
- Chat model pulled: `ollama pull llama3.2`
- Working directory: `ai/`

## Step 1 — Build the knowledge index

```sh
uv run python -m assistant.pipeline --rebuild
```

Expected output:

```
Loading documents from knowledge base...
Loaded 12 documents (4 markdown, 8 JSON)
Chunking 12 documents...
Produced 47 chunks
Embedding 47 chunks with nomic-embed-text...
Saved vector store: 47 documents → assistant/vector_store
Index built: 47 chunks
```

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
INFO: Assistant service loaded: 47 chunks in index.
```

## Step 4 — Check health

```sh
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "model_loaded": true,
  "explanation_service_available": true,
  "assistant_available": true,
  "version": "0.1.0"
}
```

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
  "answer": "The XGBoost model achieved 56.3% accuracy on the test set ...\n[source: model_card.md]",
  "sources": [
    {
      "source": "model_card.md",
      "excerpt": "Overall accuracy: 56.3% ...",
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
