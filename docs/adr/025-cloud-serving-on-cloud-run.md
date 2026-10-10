# ADR 025 — Cloud Serving on Cloud Run

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The API runs on one developer machine. It loads the models, the processed
match data and the assistant index from local paths, refreshes the data
inside the process every day (ADR 013), and talks to a local Ollama for
embeddings and chat (ADR 019). `docs/plans/hosting-plans.md` sets out to host
it for a small group of invited friends at hobby cost (a $10 monthly budget),
and `docs/plans/hosting-execution-tracker.md` orders that work.

Four things do not survive the move as they are:

1. **Where it runs.** Nothing packages the API, and `/v2/health` answers
   `status="ok"` even when the model failed to load, so a platform cannot tell
   a broken instance from a working one.
2. **Where the artifacts come from.** `ai/models/`, `datasets/processed/` and
   `ai/assistant/vector_store/` are not in Git. They exist only on the
   developer machine, so a cloud copy cannot be rebuilt or checked.
3. **Which model answers.** A cloud instance cannot reach the developer's
   Ollama, and a CPU instance cannot run a 7B model at useful speed.
4. **How data stays fresh.** The daily refresh writes to the local disk. A
   cloud container's disk is wiped on every restart and scale-to-zero.

## Decision

1. **Cloud Run, CPU only.** One container image runs the existing FastAPI app
   with one Uvicorn worker. Services scale to zero (min 0) and start with a
   maximum of one instance. Staging and production are separate services
   built from the same image digest. No GPU, Kubernetes, load balancer or
   database server.
2. **Liveness and readiness.** `/v2/live` answers 200 while the process
   serves requests. `/v2/ready` answers 200 only when every component the
   predictions need loaded at startup, and a structured 503 naming the
   missing ones otherwise. Neither probe calls the LLM provider, so a
   provider outage never restarts the service or spends quota. `/v2/health`
   stays as the diagnostics view.
3. **Immutable snapshots.** A script assembles the serving artifacts (models,
   registry, processed results and fixtures, reference data and the assistant
   index) into one directory with a `manifest.json` listing each file's path,
   size and SHA-256, the embedding model the index was built with, and the
   commit that produced it. The image copies that directory read-only. A
   snapshot is never changed after it is built; new data means a new
   snapshot. Moving snapshots to a Cloud Storage bucket, so they change
   without an image rebuild, is tracker step 2 and gets its own ADR.
4. **Provider adapters.** The assistant keeps its `Embedder` and `Generator`
   protocols. An `ASSISTANT_PROVIDER` setting chooses `ollama` (the default,
   so local development is unchanged), `workers_ai` (Cloudflare Workers AI
   over its REST API) or `off`. A hosted adapter must support tool calling
   (ADR 018), bound every call with a deadline, retry at most once, map quota,
   timeout and server errors to the existing structured 503, and report its
   token counts. Predictions never depend on the provider.
5. **One embedding space per index.** Query and document vectors must come
   from the same embedding model. The index records the model it was built
   with, and the assistant refuses to load an index built with a different
   model than the configured embedder. The cloud uses its own index, rebuilt
   with the hosted embedding model, and the 0.81 relevance cut-off is
   re-measured for it.
6. **No in-process refresh in the cloud.** Cloud services run with
   `LIVE_REFRESH_HOUR=off`. ADR 013's daily refresh stays the local default.
   In the cloud, new data arrives as a new snapshot, published by hand until
   tracker step 10 adds a scheduled job that builds, validates and promotes
   one.
7. **Safe cloud defaults.** When `K_REVISION` is set (Cloud Run sets it), the
   server refuses to start with `AUTH_REQUIRED` off or with the development
   `TELEMETRY_SALT`. Invite-only accounts (ADR 022) are always on in the
   cloud.

### Dependencies this allows

None. The image is built from the existing `ai/pyproject.toml` and lock file,
and the Workers AI adapter uses `httpx`, which is already a dependency. The
Firestore account store needs its own ADR, because it adds a client library.

## Consequences

- **Easier:** a deploy is one image digest plus one snapshot, both of which
  can be named, compared and rolled back. A broken instance fails readiness
  instead of serving 503s behind a healthy-looking `/v2/health`.
- **Harder:** the cloud and local assistants use different models and
  different indexes, so evaluation results from one do not carry over to the
  other; both assistant evals must pass against the hosted model before it
  serves traffic (ADR 019).
- **Cold starts.** Scaling to zero means the first request after idle waits
  for a full boot, including fitting the goals models. Tracker steps 0 and 6
  measure it; the plan precomputes the fits if they dominate.
- **Process-local limits.** With at most one instance, the in-memory rate
  limiter and any per-user quota are acceptable, but they reset on every
  restart. Raising the instance limit needs shared state first.
- **Stale data until step 10.** Without the in-process refresh, cloud data
  only moves when a new snapshot is published.
- **Local mode is unchanged.** Every new setting defaults to today's
  behaviour, so `uv run uvicorn backend.app.main:app` works as before.
