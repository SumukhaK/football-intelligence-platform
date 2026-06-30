# Stage 10 — Football Intelligence Assistant

**Status:** Complete  
**Date:** 2026-06-30

## What was built

A local Retrieval-Augmented Generation (RAG) assistant that answers football questions
grounded in the platform's own knowledge base — model cards, SHAP reports, evaluation
artefacts, ADRs, and feature metadata. It uses Ollama for both embeddings and
generation, a numpy-backed vector store persisted to disk, and is exposed through the
FastAPI backend at `POST /assistant/chat`.

## Architecture

```
DocumentLoader  →  TextChunker  →  OllamaEmbedder  →  VectorStore
                                                           │
                                                     cosine retrieval
                                                           │
                                               build_messages (system + user)
                                                           │
                                                   OllamaGenerator
                                                           │
                                                   AssistantResponse
```

### Key packages

| Package | Purpose |
|---|---|
| `assistant/ingestion/` | Loads `.md` and `.json` knowledge files into `Document` objects |
| `assistant/chunking/` | Splits long documents into overlapping chunks with stable SHA-1 IDs |
| `assistant/embeddings/` | `Embedder` protocol + `OllamaEmbedder` implementation |
| `assistant/retrieval/` | `VectorStore` (numpy, file-persisted) + cosine similarity `retrieve()` |
| `assistant/prompting/` | System prompt, `build_user_prompt`, `build_messages` |
| `assistant/generation/` | `Generator` protocol + `OllamaGenerator` implementation |
| `assistant/services/` | `AssistantService` — orchestrates embed → retrieve → generate |
| `assistant/pipeline.py` | `AssistantPipeline` facade: `build_index`, `load_index`, `query` |

### Backend integration

| File | Change |
|---|---|
| `backend/app/schemas/assistant.py` | `ChatRequest` / `ChatResponse` / `SourceCitation` schemas |
| `backend/app/services/chat_service.py` | Thin adapter: `AssistantService` → `ChatResponse` |
| `backend/app/routers/assistant.py` | `POST /assistant/chat` route |
| `backend/app/exceptions/__init__.py` | `AssistantNotAvailableError` + 503 handler |
| `backend/app/config.py` | 6 new Ollama/assistant config fields |
| `backend/app/schemas/common.py` | `assistant_available` field on `HealthResponse` |
| `backend/app/main.py` | Graceful assistant load in lifespan; `chat_service=None` on failure |

## Grounding and honesty

- The system prompt instructs the assistant to answer **only** from retrieved context,
  cite sources with `[source: <filename>]`, and admit when it lacks information.
- Low-relevance chunks (< 0.50 cosine similarity) are filtered before context is built.
- Confidence is reduced when the answer contains "I don't have enough information".
- The assistant never calls external APIs or invents match data.

## Configuration

All model names, paths, and generation options are configurable via environment
variables — no hardcoded values. Key settings (from `AssistantSettings`):

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_CHAT_MODEL` | `llama3.2` | Chat generation model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `ASSISTANT_VECTOR_STORE_PATH` | `assistant/vector_store` | Persisted index location |
| `ASSISTANT_TOP_K` | `5` | Top-K documents to retrieve |

## Building the index

Requires Ollama running with `nomic-embed-text` pulled:

```sh
ollama pull nomic-embed-text
cd ai
uv run python -m assistant.pipeline --rebuild
```

## Quality metrics

| Check | Result |
|---|---|
| `ruff check .` | 0 errors |
| `black --check .` | 0 changes |
| `mypy .` | 0 errors (188 source files) |
| `pytest` | 426 passed |
| New assistant tests | 52 (39 unit + 10 backend endpoint + health) |

## Tests written

- `tests/assistant/test_document.py` — 4 tests: round-trip, defaults, immutability
- `tests/assistant/test_loader.py` — 5 tests: markdown, JSON, ADR loading
- `tests/assistant/test_chunker.py` — 8 tests: single/multi chunk, overlap, chunk IDs
- `tests/assistant/test_embedder.py` — 3 tests: shape, empty input, error wrapping
- `tests/assistant/test_vector_store.py` — 9 tests: CRUD, persistence, mismatched dims
- `tests/assistant/test_retriever.py` — 6 tests: top-k, sorting, score range, empty store
- `tests/assistant/test_templates.py` — 7 tests: system prompt, citations, filtering
- `tests/assistant/test_generator.py` — 3 tests: response content, error wrapping, options
- `tests/assistant/test_assistant_service.py` — 6 tests: response shape, confidence, validation
- `tests/backend/test_assistant_endpoint.py` — 10 tests: 200, 422, 503 scenarios

All Ollama calls are mocked. Tests run without a live Ollama server.
